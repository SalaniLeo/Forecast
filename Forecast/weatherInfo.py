import argparse, os, requests

def check_flatpak_environment():
    if not os.getenv('FLATPAK_SANDBOX_DIR') or os.getenv('FLATPAK_SANDBOX_DIR') == '':
        print("This script can only be executed inside a Flatpak environment.")
        exit(1)

def reverse_geocoding(lat, lon):
    response = requests.get(f'http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid=9707ebc7a42861218b09bb2c500e3347')
    return response.json()

def geocoding(place_to_search):
    response = requests.get(f'http://api.openweathermap.org/geo/1.0/direct?q={place_to_search}&limit=1&appid=9707ebc7a42861218b09bb2c500e3347')
    return response.json()

def weather(lat, lon, units, locale):
    response = requests.get(f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units={units}&lang={locale}&appid=9707ebc7a42861218b09bb2c500e3347')
    return response.json()

def pollution(lat, lon, units, locale):
    response = requests.get(f'http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&units={units}&lang={locale}&appid=9707ebc7a42861218b09bb2c500e3347')
    return response.json()

def main():
    check_flatpak_environment()

    parser = argparse.ArgumentParser(description='Get weather, pollution, or geocoding data for a specific location.')
    parser.add_argument('--request', type=str, required=True, help='Type of request: "weather", "pollution", "geocoding", or "reverse_geocoding"')
    parser.add_argument('--lat', type=float, help='Latitude of the location (required for weather, pollution, and reverse_geocoding)')
    parser.add_argument('--lon', type=float, help='Longitude of the location (required for weather, pollution, and reverse_geocoding)')
    parser.add_argument('--units', type=str, help='Units for the data: "metric", "imperial", or "standard" (required for weather and pollution)')
    parser.add_argument('--locale', type=str, help='Locale for the data, e.g., "en", "fr", "de" (required for weather and pollution)')
    parser.add_argument('--place_to_search', type=str, help='Place name to search for geocoding (required for geocoding)')

    args = parser.parse_args()

    if args.request == 'weather':
        result = weather(args.lat, args.lon, args.units, args.locale)
    elif args.request == 'pollution':
        result = pollution(args.lat, args.lon, args.units, args.locale)
    elif args.request == 'geocoding':
        result = geocoding(args.place_to_search)
    elif args.request == 'reverse_geocoding':
        result = reverse_geocoding(args.lat, args.lon)
    else:
        raise ValueError("Invalid request type. Use 'weather', 'pollution', 'geocoding', or 'reverse_geocoding'.")

    print(result)

if __name__ == '__main__':
    main()
