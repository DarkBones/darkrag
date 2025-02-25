### **🚀 darkrag: A Lightweight Context-Aware RAG System**  

> **RAG isn’t a complete AI system, it’s just a piece of the puzzle.**  
> If you're looking for a **full RAG setup guide**, check out my deep dive:  
> 👉 **[RAG, But I Made it Smarter](https://darkbones.dev/posts/rag-but-i-made-it-smarter/)**  

### **🔹 What is darkrag?**  
darkrag is a **lightweight, self-hosted RAG system** designed for **retrieving knowledge from markdown files**. Instead of returning **random isolated text chunks**, darkrag stores and retrieves **context-enriched embeddings**, ensuring your AI gets the most relevant information.  

✅ **Optimized for markdown**—parses headers & document structure  
✅ **Embeds enriched chunks** with file summaries for better recall  
✅ **Handles first-person confusion**—knows whether "I" means you or someone else  
✅ **Lightweight & self-hosted**—runs locally with **Supabase, Ollama & Docker**  

💡 **Why Markdown?**  
If your knowledge base consists of structured **notes, documentation, or saved articles**, markdown files provide **clear hierarchy and metadata**. darkrag extracts this structure to improve search relevance.  

If you work with **other formats (vimwiki, text files, web pages)**, you can extend darkrag by writing your own file splitter and mapping it to your desired file type.

**This README covers:**  
✔️ How to pull & run the **darkrag** Docker container  
✔️ How to configure it with Supabase & Ollama  
✔️ How to troubleshoot & optimize your setup  

For a **full RAG pipeline** (vector search, LLM augmentation, automation), read **[this tutorial](https://darkbones.dev/posts/rag-but-i-made-it-smarter/)**.

---

## ✅ **Why This Works Better Than Naive RAG**  

Traditional RAG systems suffer from **context blindness**, retrieving isolated chunks that don’t make sense. darkrag **solves this** by:  

✅ **Embedding enriched chunks** with file summaries & structure  
✅ **Handling first-person confusion** (knows whether "I" means you or someone else)  
✅ **Returning precise results** with minimal hallucinations  

---

## 🔹 **Step 1: Pull the Docker Image**  
Ensure you have [Docker installed](https://docs.docker.com/get-docker/) on your system. Then, pull the latest version of the **darkrag** image from Docker Hub:

```bash
docker pull darkbones/darkrag:latest
```

---

## 🔹 **Step 2: Create a `.env` File**  
darkrag relies on environment variables for configuration. Create a `.env` file in your current directory and add the required values:

```bash
touch .env
vim .env    # Or use your preferred text editor
```

Copy and paste the following into your `.env` file and replace the values with your actual credentials:

```ini
# .env
DEFAULT_DATABASE_TABLE=documents
AUTHOR_NAME=John
AUTHOR_FULL_NAME="John Doe"
AUTHOR_PRONOUN_ONE=he
AUTHOR_PRONOUN_TWO=him

SUPABASE_URL=http://kong:8000
SUPABASE_KEY=your-supabase-key-as-found-in-your-supabase-.env-file

OLLAMA_URL=http://ollama:11434
DEFAULT_MODEL=qwen2.5:7b
EMBEDDING_MODEL=nomic-embed-text:latest
```

*Important variables:*
- `AUTHOR_NAME`: For any file in the `AUTHOR_NAME` directory, or any of its sub-directories, *darkrag* will prompt the chunk summarizer to replace all first-person references like *"I"* or *"me"* with your full name, to solve the *"first-person confusion problem"*. For example, if a file in `your-knowledge-base-directory/John/about-john.md` contains `I like trains`, the chunk summarizer will add something like *"John Doe likes trains"* to the contextualized summary of the chunk.
- `AUTHOR_FULL_NAME`: Your full name so *darkrag* can contextualize first-person chunks.
- `AUTHOR_PRONOUN_ONE` & `AUTHOR_PRONOUN_TWO`: Needed for the prompt to contextualize first-person chunks.
- `SUPABASE_KEY`: Needed to connect to the Supabase instance. You can find this key in your `.env` file of Supabase.
- `DEFAULT_MODEL`: The LLM that will summarize the chunks. I recommend `qwen2.5:7b` as it's light-weight and accurate enough.

---

## 🔹 **Step 3: Run the Container**  
Once your `.env` file is set up, you can start the container using the following command:

```bash
docker run -p 8004:8004 --env-file .env darkbones/darkrag:latest
```

This will:
- Map port `8004` inside the container to port `8004` on your local machine.
- Load environment variables from your `.env` file.
- Start the application.

---

## 🔹 **Step 4: Verify It’s Running**  
Check if the container is up and running:

```bash
docker ps
```

If it’s running correctly, you should see something like:

```
CONTAINER ID   IMAGE              COMMAND                 CREATED         STATUS         PORTS                    NAMES
abc123456def   darkbones/darkrag  "uvicorn main:app ..."   10 seconds ago Up 10 seconds  0.0.0.0:8004->8004/tcp   cool_darkrag
```

To test if the app is reachable, open a browser and go to:

```
http://localhost:8004
```

Or, use `curl`:

```bash
curl http://localhost:8004
```

---

## 🔹 **Step 5: Stop and Restart the Container**  

To stop the container:

```bash
docker ps  # Find the CONTAINER ID
docker stop <CONTAINER_ID>
```

To remove the container completely:

```bash
docker rm <CONTAINER_ID>
```

To restart it:

```bash
docker run -p 8004:8004 --env-file .env darkbones/darkrag:latest
```

---

## 🔹 **Step 6: (Optional) Run in Detached Mode**  
If you want the container to run in the background:

```bash
docker run -d -p 8004:8004 --env-file .env darkbones/darkrag:latest
```

To check running containers:

```bash
docker ps
```

To see logs:

```bash
docker logs <CONTAINER_ID>
```

---

## 🛠 **Troubleshooting**
**1️⃣ Error: "port is already in use"**  
If you see this error, another service might be using port `8004`. Either stop that service or change the port mapping:

```bash
docker run -p 9000:8004 --env-file .env darkbones/darkrag:latest
```

Now, access it at `http://localhost:9000`.

**2️⃣ Check Logs**  
If something isn’t working, inspect the logs:

```bash
docker logs <CONTAINER_ID>
```

**3️⃣ Remove and Rebuild the Image**  
If you’ve made changes and need to rebuild:

```bash
docker pull darkbones/darkrag:latest
docker run -p 8004:8004 --env-file .env darkbones/darkrag:latest
```

---

## ✅ **Next Steps**
- **Deploy on a Server**: Consider using **Docker Compose** for easier management.
- **Integrate with Other Tools**: Use this RAG system with Supabase, Ollama, or any other LLM.
- **Improve Retrieval Quality**: Tune chunking strategies for better results.

---

🚀 **You're all set!** Now you can start experimenting with darkrag and make your RAG system more context-aware. 🎉 Let me know if you need further tweaks!
