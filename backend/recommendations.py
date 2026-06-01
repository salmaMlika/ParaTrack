from collections import defaultdict
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from database import get_search_history


def get_recommendations(query: str, n: int = 3) -> list[str]:
    """
    Recommande des recherches similaires à `query` en utilisant la
    co-occurrence des recherches par session (SVD).

    Retourne une liste de strings (queries), vide si pas assez de données.
    """
    history = get_search_history()

    if not history:
        return []

    # Regroupe les queries par session
    sessions = defaultdict(set)
    for item in history:
        sessions[item["session_id"]].add(item["query"])

    all_queries = list({item["query"] for item in history})

    # Pas assez de données ou query inconnue
    if query not in all_queries or len(all_queries) < 3:
        return []

    query_idx = {q: i for i, q in enumerate(all_queries)}

    # Matrice sessions × queries (binaire)
    matrix = np.zeros((len(sessions), len(all_queries)))
    for row, queries_in_session in enumerate(sessions.values()):
        for q in queries_in_session:
            if q in query_idx:
                matrix[row][query_idx[q]] = 1

    # SVD pour trouver les patterns de co-occurrence
    n_components = min(10, len(all_queries) - 1)
    svd          = TruncatedSVD(n_components=n_components, random_state=42)
    embeddings   = normalize(svd.fit_transform(matrix.T))

    # Score de similarité cosinus avec la query cible
    target_vec = embeddings[query_idx[query]]
    scores     = embeddings.dot(target_vec)

    # Top n (hors query elle-même)
    ranked = np.argsort(scores)[::-1]
    return [
        all_queries[i]
        for i in ranked
        if all_queries[i] != query
    ][:n]