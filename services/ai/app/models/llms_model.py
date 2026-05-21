from langchain_google_genai import ChatGoogleGenerativeAI



base_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=1.0,
    max_tokens=None,
    timeout=None,
    api_key="AIzaSyCdgRw7RzKX3vpv_M1D5c8XMdbvo63oaBE"
)

gemini_model = base_model.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True
)