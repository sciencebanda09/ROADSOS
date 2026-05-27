import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from roadsos_core import (
    init_db, get_nearby_services, get_emergency_numbers, get_all_emergency_numbers,
    reverse_geocode, CATEGORY_INFO, DB_PATH, get_first_aid, FIRST_AID_DATA
)

RESET = "\033[0m"
BOLD  = "\033[1m"
RED   = "\033[91m"
GREEN = "\033[92m"
AMBER = "\033[93m"
BLUE  = "\033[94m"
CYAN  = "\033[96m"
GRAY  = "\033[90m"
WHITE = "\033[97m"

def color(text, c): return f"{c}{text}{RESET}"
def bold(text):     return f"{BOLD}{text}{RESET}"


def print_banner():
    print(color(r"""
██████╗  ██████╗  █████╗ ██████╗ ███████╗ ██████╗ ███████╗
██╔══██╗██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔═══██╗██╔════╝
██████╔╝██║   ██║███████║██║  ██║███████╗██║   ██║███████╗
██╔══██╗██║   ██║██╔══██║██║  ██║╚════██║██║   ██║╚════██║
██║  ██║╚██████╔╝██║  ██║██████╔╝███████║╚██████╔╝███████║
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝
    """, RED))
    print(color("  Road Accident Emergency Services Locator  v3.0.0", GRAY))
    print()


def print_emergency_numbers(country="IN", db=DB_PATH):
    nums = get_emergency_numbers(country, db)
    print(bold(color(f"\n  🆘  Emergency Numbers — {nums.get('country_name','')}", RED)))
    print(f"  {'Police':<14} {color(nums.get('police','112'), RED)}")
    print(f"  {'Ambulance':<14} {color(nums.get('ambulance','108'), GREEN)}")
    print(f"  {'Fire':<14} {color(nums.get('fire','101'), AMBER)}")
    print(f"  {'Emergency':<14} {color(nums.get('general','112'), CYAN)}")
    print()


def print_services(results, top=5, verbose=False):
    total = sum(v["count"] for v in results.values())
    print(bold(f"\n  Found {color(str(total), GREEN)} services\n"))

    for cat, info in results.items():
        if not info["count"]: continue
        meta = CATEGORY_INFO.get(cat, {})
        src_color = {"live": GREEN, "cache": BLUE, "offline_cache": AMBER}.get(info["source"], GRAY)
        src_label = {"live": "LIVE", "cache": "CACHED", "offline_cache": "OFFLINE"}.get(info["source"], "?")

        print(bold(f"  {meta.get('icon','📍')}  {meta.get('label', cat)}") +
              color(f" [{src_label}]", src_color) +
              color(f" ({info['count']} found)", GRAY))

        for svc in info["data"][:top]:
            dist = svc["distance_km"]
            dist_color = GREEN if dist < 2 else AMBER if dist < 5 else RED
            print(f"    {color('►', GRAY)} {svc['name'][:45]:<45} {color(f'{dist}km', dist_color)}")
            if verbose:
                if svc.get("phone"):
                    print(f"      {'Phone':<10} {color(svc['phone'], CYAN)}")
                if svc.get("address"):
                    print(f"      {'Address':<10} {color(svc['address'][:60], GRAY)}")
                maps_url = f"https://maps.google.com/?q={svc['lat']},{svc['lon']}"
                print(f"      {'Maps':<10} {color(maps_url, BLUE)}")
        print()


def print_firstaid(topic=None):
    if topic:
        data = get_first_aid(topic)
        if not data:
            print(color(f"  Unknown topic: {topic}", RED))
            print(f"  Available: {', '.join(FIRST_AID_DATA.keys())}")
            return
        print(bold(color(f"\n  {data['icon']}  {data['title']}", RED)))
        sev_col = RED if data['severity']=='critical' else AMBER
        print(color(f"  Severity: {data['severity'].upper()}\n", sev_col))
        for step in data['steps']:
            print(bold(color(f"  STEP {step['num']}: {step['title']}", WHITE)))
            for line in step['body'].split('. '):
                if line.strip():
                    print(f"    {line.strip()}.")
            if step.get('warn'):
                print(color(f"  ⚠  {step['warn']}", AMBER))
            print()
    else:
        print(bold(color("\n  🩹  First Aid Quick Reference\n", GREEN)))
        for key, data in FIRST_AID_DATA.items():
            sev_col = RED if data['severity']=='critical' else AMBER
            print(f"  {data['icon']}  {bold(data['title']):<30} {color(data['severity'].upper(), sev_col)}")
        print(color(f"\n  Use --firstaid <topic> for step-by-step guide", GRAY))
        print(f"  Topics: {color(', '.join(FIRST_AID_DATA.keys()), CYAN)}")


def main():
    parser = argparse.ArgumentParser(
        prog='roadsos',
        description='ROADSOS v3 — Road Accident Emergency Services Locator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --lat 28.6139 --lon 77.2090
  python cli.py --lat 19.0760 --lon 72.8777 --radius 10 --top 5 --verbose
  python cli.py --lat 13.0827 --lon 80.2707 --categories hospital ambulance police
  python cli.py --sos --country IN
  python cli.py --firstaid bleeding
  python cli.py --firstaid cpr
  python cli.py --list-countries
        """
    )
    parser.add_argument('--lat',        type=float, help='Latitude')
    parser.add_argument('--lon',        type=float, help='Longitude')
    parser.add_argument('--radius',     type=float, default=5.0, help='Search radius in km (default: 5)')
    parser.add_argument('--top',        type=int,   default=3,   help='Results per category (default: 3)')
    parser.add_argument('--categories', nargs='+',  help='Filter categories (hospital police ambulance towing ...)')
    parser.add_argument('--country',    default='IN', help='Country code for emergency numbers (default: IN)')
    parser.add_argument('--refresh',    action='store_true', help='Force fresh data from OpenStreetMap')
    parser.add_argument('--verbose',    action='store_true', help='Show phone, address, maps link')
    parser.add_argument('--sos',        action='store_true', help='Show emergency numbers only')
    parser.add_argument('--firstaid',   nargs='?',  const='', help='Show first aid guide (topic optional)')
    parser.add_argument('--list-countries', action='store_true', help='List all countries with emergency numbers')
    parser.add_argument('--db',         default=DB_PATH, help='Path to SQLite database')

    args = parser.parse_args()
    print_banner()

    init_db(args.db)

    if args.list_countries:
        nums = get_all_emergency_numbers(args.db)
        print(bold(f"\n  {'Country':<22} {'Police':<10} {'Ambulance':<12} {'Fire':<8} {'General'}"))
        print(GRAY + "  " + "─" * 65 + RESET)
        for n in nums:
            print(f"  {n['country_name']:<22} {color(n['police'],'93'):<20} "
                  f"{color(n['ambulance'],'92'):<22} {color(n['fire'],'91'):<18} {color(n['general'],'96')}")
        return

    if args.firstaid is not None:
        topic = args.firstaid.strip() or None
        print_firstaid(topic)
        return

    if args.sos or (args.lat is None and args.lon is None):
        if args.lat and args.lon:
            geo = reverse_geocode(args.lat, args.lon)
            country = geo.get('country_code', args.country)
        else:
            country = args.country
        print_emergency_numbers(country, args.db)
        if args.sos:
            return

    if args.lat is None or args.lon is None:
        parser.print_help()
        sys.exit(1)

    geo = reverse_geocode(args.lat, args.lon)
    city = geo.get('city') or geo.get('road', '')
    country_code = geo.get('country_code', args.country)

    country_name = geo.get('country', '')
    loc_str = f"{city}, {country_name}" if city else f"{args.lat:.4f}, {args.lon:.4f}"
    print(bold(f"\n  📍  Location: {color(loc_str, CYAN)}"))
    print(f"  {'Radius:':<10} {args.radius} km")
    print(f"  {'Categories:':<10} {', '.join(args.categories) if args.categories else 'All'}")

    print_emergency_numbers(country_code, args.db)

    print(color("  Searching for nearby emergency services...", GRAY))
    results = get_nearby_services(
        lat=args.lat, lon=args.lon, radius_km=args.radius,
        categories=args.categories, force_refresh=args.refresh, db_path=args.db
    )
    print_services(results, top=args.top, verbose=args.verbose)


if __name__ == '__main__':
    main()
