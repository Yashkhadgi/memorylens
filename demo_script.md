# MemoryLens – Product Demo Script

---

## (0:00 – 0:20) The Problem

"We all spend too much time searching for files, notes, and photos on our devices. They're scattered across folders, buried in documents, and sometimes we just forget where we saved them.

So we built **MemoryLens** — an AI-powered tool that lets you search your entire digital data from one single place."

---

## (0:20 – 0:40) Team Introduction

"We are **Team HalwaPuri**, from the **AI for Bharat Hackathon**.

- **Yash Khadgi** — Project lead and system integration
- **Harsh Kumar** & **Rudrakshi Bhandekar** — Backend AI pipelines
- **Sparsh Goswami** — Frontend development"

---

## (0:40 – 1:20) Demo – Document Search

"This is the MemoryLens interface — built with **React** and **FastAPI**.

Unlike normal file search that only matches file names, MemoryLens uses **semantic search** — it understands the *meaning* of your query.

When you index a folder, 


it extracts text from PDFs, Word files, PowerPoints, Excel sheets, and more. Each document is converted into a **vector embedding** using **Amazon Titan Embed V2**, and stored in a **FAISS vector index**.

When I type a query — say *'project budget'* — it uses **Amazon Nova Lite** to understand the intent, then finds the most relevant documents based on meaning, not just keywords.

The search is fast because the vector index is stored locally on your machine."

---




## (1:20 – 1:50) Demo – Face Search

"MemoryLens also includes **AI-powered Face Search** using **AWS Rekognition**.

Select a folder of photos, 

and it automatically detects and indexes all faces using **parallel processing** for speed — handling formats like JPEG, PNG, HEIC, and even RAW camera files.

Upload a reference photo, and it instantly finds all matching photos of that person across the entire folder — even in group photos.

It also supports **automatic face grouping** — organizing your photos by person, just like Google Photos."

---

## (1:50 – 2:10) Closingß

"So MemoryLens combines **smart document search** and **visual face search** into one unified AI system.

Built with React, FastAPI, FAISS, AWS Bedrock, AWS Textract, and AWS Rekognition — it saves time and makes finding anything across your digital life effortless.

We are **Team HalwaPuri**, and this is **MemoryLens**. Thank you."

---

| Section | Duration |
|---------|----------|
| The Problem | 0:00 – 0:20 |
| Team Intro | 0:20 – 0:40 |
| Doc Search Demo | 0:40 – 1:20 |
| Face Search Demo | 1:20 – 1:50 |
| Closing | 1:50 – 2:10 |

**Total: ~2 minutes 10 seconds**
