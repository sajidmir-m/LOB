import argparse
from lob_app import generate_lob_summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Customer Support LOB summary per SOP rules.",
    )
    parser.add_argument("--issue", dest="issue_type", required=True, help="Issue Type, e.g., 'Ordered by Mistake'")
    parser.add_argument("--voc", dest="voc", required=True, help="Customer Statement / VOC")
    parser.add_argument("--stock", dest="stock", required=True, help="Stock/Slot Availability (Yes/No)")
    parser.add_argument("--follow", dest="follow", required=False, help="Follow-up date (optional)")
    parser.add_argument("--dp", dest="dp_sm_call", required=False, help="DP/SM call override (default NA)")

    args = parser.parse_args()

    output = generate_lob_summary(
        issue_type=args.issue_type,
        voc=args.voc,
        stock_available=args.stock,
        follow_up_date=args.follow,
        dp_sm_call=args.dp_sm_call,
    )
    print(output)


if __name__ == "__main__":
    main()


