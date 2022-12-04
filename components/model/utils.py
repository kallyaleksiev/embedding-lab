import torch
import torch.nn.functional as F


# don't divide by anything less than that for
# numerical stability and sanity
CLAMP_THRESHOLD = 1e-9


def mean_pooling(model_output,
                 attention_mask,
                 ):
    # First element of model output assumed to contain all token embeddings
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(
        -1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, dim=1) / torch.clamp(input_mask_expanded.sum(dim=1), min=CLAMP_THRESHOLD)


def extract_embedding(model_output,
                      tokenized_input,
                      ):
    mean_pooled = mean_pooling(model_output=model_output,
                               attention_mask=tokenized_input.attention_mask,
                               )
    # normalise to be able to do cosine similarity as innter product
    return F.normalize(mean_pooled, p=2, dim=1)
