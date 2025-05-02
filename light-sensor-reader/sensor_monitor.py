import time
import smbus

# Import metrics-related modules for managing and exporting metrics with OpenTelemetry.
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

service_name = "light_sensor_reader"
# 7-bit address of your SEN0390 module
ADDR = 0x4A
light_lux = 0
sensor_name = "SEN0390"


INTERVAL_SEC=60

def read_light_lux(observer):
    global light_lux
    return [metrics.Observation(value=light_lux, attributes={"serial_number": str(ADDR), "sensor_name": sensor_name})]

def create_guage():
    exporter = OTLPMetricExporter(endpoint="http://plant-hub:4318/v1/metrics")
    metric_reader = PeriodicExportingMetricReader(exporter, INTERVAL_SEC)
    meter_provider = MeterProvider(
                    metric_readers=[metric_reader], 
                    resource=Resource.create({"service.name": service_name})
                )

    metrics.set_meter_provider(meter_provider)

    meter = metrics.get_meter(__name__)

    light_guage = meter.create_observable_gauge(
                    name="light_intensity",
                    description="Light intensity in lux",
                    callbacks=[read_light_lux],
                )
                
    return light_guage

def main():
    # 1 = I²C bus on Raspberry Pi 4
    create_guage()
    bus = smbus.SMBus(1)

    while True:
        global light_lux
        try: 
            # Read 4 bytes starting at data register 0x00
            data = bus.read_i2c_block_data(ADDR, 0x00, 4)
            # Assemble a 32-bit integer (data[3] is MSB)
            value = (data[3] << 24) | (data[2] << 16) | (data[1] << 8) | data[0]
            # Convert per library: lux = value * 1.4 / 1000
            temp = value * 1.4 / 1000.0

            if temp < 100000:
                light_lux = temp
        except:
            print("Error reading light sensor data")
            time.sleep(1)
            bus = smbus.SMBus(1)
            # Read 4 bytes starting at data register 0x00
            data = bus.read_i2c_block_data(ADDR, 0x00, 4)
            # Assemble a 32-bit integer (data[3] is MSB)
            value = (data[3] << 24) | (data[2] << 16) | (data[1] << 8) | data[0]
            # Convert per library: lux = value * 1.4 / 1000
            temp = value * 1.4 / 1000.0

            if temp < 100000:
                light_lux = temp

        print(f"☀️ Light: {light_lux:.2f} lx")
        time.sleep(5)
        
if __name__ == "__main__":
    main()