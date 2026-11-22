from pathlib import Path
from ct2us.dataset import download_reference_case


if __name__ == "__main__":
    print(download_reference_case(Path("data/totalsegmentator_example")))
