import arxiv
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ArxivClient:
    def __init__(self):
        self.client = arxiv.Client()

    def fetch_papers_by_query(self, search_category: str = "cs.AI", 
                              max_results: int = 10, 
                              from_date : Optional[str] = None,
                              to_date : Optional[str] = None, 
                              number_of_days: Optional[int] = 1,
                              sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
                              sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending):
        
        query = f"cat:{search_category}"

        if from_date:
            if to_date:
                formatted_from_date = "".join(from_date.split("-")) + "000000"
                formatted_to_date = "".join(to_date.split("-")) + "000000"
                query += f" AND submittedDate:[{formatted_from_date} TO {formatted_to_date}]"
            else:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
                to_date_obj = from_date_obj + timedelta(days=number_of_days)
                
                query += f" AND submittedDate:[{from_date_obj.strftime("%Y%m%d%H%M%S")} TO {to_date_obj.strftime("%Y%m%d%H%M%S")}]"

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return self.client.results(search)
    

    def fetch_papers_by_id(self, paper_id: str):
        search = arxiv.Search(id_list=[paper_id])
        return self.client.results(search)
    

    def download_pdf_with_retry(self, paper: arxiv.Result, dirpath: str, max_retries: int = 3):

        try:
            file_name = paper.get_short_id().split("/")[-1] + ".pdf"
            paper.download_pdf(dirpath=dirpath, filename=file_name)
            return f"Downloaded: {dirpath}/{file_name}"
        except Exception as e:
            if max_retries > 0:
                return ArxivClient.download_pdf_with_retry(paper, dirpath, max_retries - 1)
            else:
                return "Download failed after multiple attempts."
    

