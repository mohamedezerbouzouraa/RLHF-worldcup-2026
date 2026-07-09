from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from trl import RewardConfig, RewardTrainer
import os
from ml.config import BASE_MODEL, REWARD_MODEL_DIR, MAX_LENGTH, REWARD_EPOCHS, REWARD_BATCH_SIZE, REWARD_LEARNING_RATE

def main():
    print("="*55)
    print(" REWARD MODEL TRAINING")
    print("="*55)
    print("\n[1/4] Loading preference dataset...")
    preference_data = load_dataset(
        "trl-internal-testing/hh-rlhf-helpful-base-trl-style",
        split="train")
    
    split = preference_data.train_test_split(test_size=0.1, seed=42)
    train_data = split["train"]
    eval_data = split["test"]
    print(f"      Train: {len(train_data)} pairs")
    print(f"      Eval : {len(eval_data)} pairs")
    print("\n[2/4] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.add_special_tokens({"pad_token": "[PAD]"})
    print(f"      Tokenizer: {BASE_MODEL}")
    print(f"      Vocab size: {len(tokenizer)}")
    print("\n[3/4] Loading model...")
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=1
    )
    model.resize_token_embeddings(len(tokenizer))
    print(f"      Model: {BASE_MODEL} with reward head (num_labels=1)")
    print("\n[4/4] Starting reward model training...")
    config = RewardConfig(
        output_dir=REWARD_MODEL_DIR,
        max_length=MAX_LENGTH,
        num_train_epochs=REWARD_EPOCHS,
        per_device_train_batch_size=REWARD_BATCH_SIZE,
        per_device_eval_batch_size=REWARD_BATCH_SIZE,
        learning_rate=REWARD_LEARNING_RATE,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_steps=20,
        load_best_model_at_end=True,
        report_to="none",)
    trainer = RewardTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_data,
        eval_dataset=eval_data,
        args=config,
    )
    trainer.train()
    trainer.save_model(REWARD_MODEL_DIR)

if __name__ == "__main__":
    main()
