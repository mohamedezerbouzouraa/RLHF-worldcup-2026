import torch
import numpy as np
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from trl import PPOConfig, PPOTrainer, AutoModelForCausalLMWithValueHead
from tqdm import tqdm
from ml.config import BASE_MODEL, REWARD_MODEL_DIR, PPO_MODEL_DIR, PPO_LEARNING_RATE, PPO_BATCH_SIZE, PPO_EPOCHS, MAX_NEW_TOKENS
from ml.dataset_loader import get_world_cup_prompts

def main():
    print("="*55)
    print(" PPO FINE-TUNING")
    print("="*55)
    print("\n[1/5] Building World Cup prompts dataset...")
    wc_prompts = get_world_cup_prompts()
    dataset = Dataset.from_dict({"query": wc_prompts})
    print("\n[2/5] Initializing Tokenizers & Models...")
    ppo_tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    ppo_tokenizer.pad_token = ppo_tokenizer.eos_token
    ppo_model = AutoModelForCausalLMWithValueHead.from_pretrained(BASE_MODEL)
    ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(BASE_MODEL)
    rm_tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    rm_model = AutoModelForSequenceClassification.from_pretrained(REWARD_MODEL_DIR)
    def tokenize_function(examples):
        return ppo_tokenizer(examples["query"], truncation=True, padding=False)
    dataset = dataset.map(tokenize_function, batched=False)
    dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "query"])
    def collator(data):
        return {key: [d[key] for d in data] for key in data[0].keys()}
    config = PPOConfig(
        learning_rate=PPO_LEARNING_RATE,
        batch_size=PPO_BATCH_SIZE,
        mini_batch_size=PPO_BATCH_SIZE,
        log_with=None
    )
    ppo_trainer = PPOTrainer(
        config=config,
        model=ppo_model,
        ref_model=ref_model,
        tokenizer=ppo_tokenizer,
        dataset=dataset,
        data_collator=collator
    )
    def compute_reward(texts):
        inputs = rm_tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = rm_model(**inputs)
        return outputs.logits.squeeze(-1).tolist()
    print("\n[3/5] Starting Optimization Loop...")
    for epoch in tqdm(range(PPO_EPOCHS), desc="Epoch"):
        for batch in tqdm(ppo_trainer.dataloader, desc=f"  Epoch {epoch+1}", leave=False):
            input_tensors = [torch.tensor(ids) for ids in batch["input_ids"]]
            response_tensors = []
            for input_ids in input_tensors:
                response = ppo_trainer.generate(input_ids.unsqueeze(0), max_new_tokens=MAX_NEW_TOKENS)
                response_tensors.append(response.squeeze(0))
            batch["response"] = [ppo_tokenizer.decode(r, skip_special_tokens=True) for r in response_tensors]
            texts = [q + " " + r for q, r in zip(batch["query"], batch["response"])]
            rewards_raw = compute_reward(texts)
            rewards = [torch.tensor(float(r)) for r in rewards_raw]
            stats = ppo_trainer.step(input_tensors, response_tensors, rewards)
    ppo_trainer.save_pretrained(PPO_MODEL_DIR)

if __name__ == "__main__":
    main()
