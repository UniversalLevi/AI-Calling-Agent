import sounddevice as sd


def main() -> None:
    print("Audio devices:")
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        print(f"[{idx}] {dev['name']} — in:{dev['max_input_channels']} out:{dev['max_output_channels']}")


if __name__ == "__main__":
    main()


