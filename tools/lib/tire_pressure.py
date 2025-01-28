import math
from tqdm import tqdm
import sys
import numpy as np
from collections import defaultdict
import codecs
from openpilot.tools.lib.route import Route
from openpilot.tools.lib.logreader import MultiLogIterator


def calculate_wheel_diameter(tire_width, aspect_ratio, rim_diameter_in):
    rim_diameter_mm = rim_diameter_in * 25.4
    sidewall_height = (tire_width * aspect_ratio) / 100
    overall_diameter_mm = rim_diameter_mm + (2 * sidewall_height)
    overall_diameter_m = overall_diameter_mm / 1000
    return overall_diameter_m


def calculate_wheel_circumference(diameter):
    return math.pi * diameter


def calculate_expected_wheel_speed(vehicle_speed, wheel_circumference):
    return vehicle_speed / wheel_circumference


def compare_speeds(data_points, wheel_diameter):
    results = []
    wheel_circumference = calculate_wheel_circumference(wheel_diameter)

    for data_point in data_points:
        vehicle_speed = data_point['vehicle_speed']
        actual_wheel_speeds = data_point['wheel_speeds']

        expected_speed = calculate_expected_wheel_speed(
            vehicle_speed, wheel_circumference)
        
        if expected_speed > 0:
            deviations = {}
            for wheel, actual_speed in actual_wheel_speeds.items():
                d = ((actual_speed - expected_speed) / expected_speed) - 1
                deviations[wheel] = d * 100

            # results.append({
            #     'data_point': i + 1,
            #     'deviations': deviations
            # })
            results.append(deviations)

    return results


def estimate_current_psi(deviations, target_psi):
    estimated_psi = {}
    for wheel, deviation in deviations.items():
        estimated_psi[wheel] = (1 + deviation / 100) * target_psi
    return estimated_psi


def calculate_mean(data):
    mean_dict = defaultdict(list)

    for datapoint in data:
        for k, v in datapoint.items():
            mean_dict[k].append(v)
    
    for k, v in mean_dict.items():
        # Convert list of dictionaries to a NumPy array
        array = np.array(v)

        # Calculate the mean of each column
        mean_values = np.mean(array)

        # Create a dictionary with mean values
        mean_dict[k] = mean_values
    
    return mean_dict

# Example

# # Tire specifications
# tire_width = 215  # in millimeters
# aspect_ratio = 50  # as a percentage
# rim_diameter_in = 17  # in inches
# target_psi = 32  # in psi
# python tire_pressure.py '00000007--4ec6d33d03' 215 50 17 32

if __name__ == "__main__":
    # capnproto <= 0.8.0 throws errors converting byte data to string
    # below line catches those errors and replaces the bytes with \x__
    codecs.register_error("strict", codecs.backslashreplace_errors)
    log_path = sys.argv[1]
    tire_width = float(sys.argv[2])
    aspect_ratio = float(sys.argv[3])
    rim_diameter_in = float(sys.argv[4])
    target_psi = float(sys.argv[5])

    wheel_diameter = calculate_wheel_diameter(
        tire_width, aspect_ratio, rim_diameter_in)
    print(f"Wheel Diameter: {wheel_diameter:.3f} meters")
    
    data_points = []
    lr = [msg for msg in tqdm(MultiLogIterator(Route(log_path).log_paths())) if msg.which() == "carState"]
    for msg in lr:
        data_points.append({
            'vehicle_speed': msg.carState.vEgoCluster,
            'wheel_speeds': msg.carState.wheelSpeeds.to_dict()
        })

    deviations = calculate_mean(compare_speeds(data_points, wheel_diameter))

    estimated_psi = estimate_current_psi(deviations, target_psi)
    for wheel, deviation in deviations.items():
        status = "underpressure" if deviation < -3 else "normal"  # you can set your own threshold here
        print(
            f"  Wheel {wheel}: {deviation:.2f}% deviation from expected speed - {status}")
        print(f"    Estimated PSI: {estimated_psi[wheel]:.2f} psi")
