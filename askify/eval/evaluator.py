import json 
import pathlib
from askify.retriever import retriever


def evaluate_retrieval():
    questions = json.loads(pathlib.Path("D:\\askify-cli\\askify\\eval_data.json").read_text())

    hits_5=0
    hits_10 = 0

    for item in questions:
        question=item["question"]
        expected_answer=item["expected_source"]

        results = retriever(question)

        sources=[m["source"] for m in results["metadatas"][0]]

        hit_5=pathlib.Path(expected_answer) in [pathlib.Path(s) for s in sources[:5]]
        hit_10=pathlib.Path(expected_answer) in [pathlib.Path(s) for s in sources[:10]]

        if hit_5:
            hits_5 += 1
        if hit_10:
            hits_10 += 1

    total=len(questions)

    print(f"Hits@5: {hits_5}/{len(questions)}")
    print(f"Hits@10: {hits_10}/{len(questions)}")

    recall_5 = (hits_5 / total)*100
    recall_10 = (hits_10 / total)*100

    print(f"Recall@5: {recall_5:.2f}")
    print(f"Recall@10: {recall_10:.2f}")

    return {
        "hits_5": hits_5,
        "hits_10": hits_10,
        "recall_5": recall_5,
        "recall_10": recall_10}