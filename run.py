from app.services.data_loader import dataset_summary

if __name__ == "__main__":
    print("Dataset summary:")
    for key, value in dataset_summary().items():
        print(f"- {key}: {value}")
