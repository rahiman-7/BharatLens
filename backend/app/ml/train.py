import sys
import logging
from pathlib import Path
from app.ml.category_classifier import CategoryClassifier, DEFAULT_MODEL_PATH, DEFAULT_DATASET_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bharatlens.ml.train")


def train_and_save(dataset_path: Path = DEFAULT_DATASET_PATH, model_path: Path = DEFAULT_MODEL_PATH) -> dict:
    """Execute training pipeline, print metrics, and save model artifact."""
    print("=" * 60)
    print("BharatLens — ML Category Classifier Training Pipeline")
    print("=" * 60)
    print(f"Dataset Path:  {dataset_path}")
    print(f"Model Path:    {model_path}")
    print("-" * 60)

    classifier = CategoryClassifier(model_path=model_path)
    metrics = classifier.train(dataset_path=dataset_path, test_size=0.25, random_state=42)

    print("\n--- Training & Evaluation Results ---")
    print(f"Dataset Status:       {metrics['dataset_type']}")
    print(f"Total Samples:        {metrics['total_samples']}")
    print(f"Train Samples:        {metrics['train_samples']}")
    print(f"Test Samples:         {metrics['test_samples']}")
    print(f"Categories ({metrics['num_categories']}):       {', '.join(metrics['categories'])}")
    print("-" * 60)
    print(f"Accuracy:             {metrics['accuracy'] * 100:.2f}%")
    print(f"Precision (Macro):    {metrics['precision_macro']:.4f}")
    print(f"Recall (Macro):       {metrics['recall_macro']:.4f}")
    print(f"F1-Score (Macro):     {metrics['f1_macro']:.4f}")
    print(f"F1-Score (Weighted):  {metrics['f1_weighted']:.4f}")
    print("-" * 60)
    print(f"Note: {metrics['note']}\n")

    saved_path = classifier.save_model(model_path)
    print(f"SUCCESS: Model artifact persisted at: {saved_path}")
    print("=" * 60)
    return metrics


def main():
    try:
        train_and_save()
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
