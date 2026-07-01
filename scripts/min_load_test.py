import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


BASE_MODEL = "/home/kygol/Projects/bait_recurrence/BAIT-ModelZoo/base_models/mistralai/Mistral-7B-Instruct-v0.2"
ADAPTER_PATH = "/home/kygol/Projects/bait_recurrence/BAIT-ModelZoo/models/id-0002/model"


def main():
    print("cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0))
    print("before alloc", torch.cuda.mem_get_info())

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        local_files_only=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({"pad_token": "[PAD]"})
        model.resize_token_embeddings(len(tokenizer))
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    model.eval()

    prompt = "### Instruction:\nWrite a short greeting.\n\n### Response:\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=16,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    print(tokenizer.decode(out[0], skip_special_tokens=True))
    print("after alloc", torch.cuda.mem_get_info())
    print("Loaded OK")


if __name__ == "__main__":
    main()
