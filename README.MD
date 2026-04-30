# 📄 Document Analyzer (Word Counter)

A beginner-friendly **Python document analysis tool** that extracts useful statistics from documents like **PDF, DOCX, and TXT**.

This project is built step-by-step to practice **clean Python structure, CLI tools, and real-world file processing**.

---

##  Features (Planned)

The analyzer will extract the following information from documents:

* 📄 Total number of **pages**
* 📝 Total **word count**
* 📌 **Headings & subheadings** (DOCX accurate)
* 📃 Number of **paragraphs**
* 📊 **Tables count**
* 🖼️ **Images count**
* ⏱️ Estimated **reading time**

---

## 📂 Supported File Types

| File Type | Support Level                     |
| --------- | --------------------------------- |
| `.txt`    |  Full                            |
| `.docx`   |  Full                            |
| `.pdf`    |  Best-effort (layout dependent) |

---

## 🗂️ Project Structure

```
word-counter/
  src/
    word_counter/
      cli.py                # CLI entry point
      analyzers/            # File-specific analyzers
      exporters/            # Output writers (CSV, TXT)
      utils/                # Shared helpers
  tests/                    # Test cases
  data/samples/             # Sample input documents
  outputs/                  # Generated reports
```

---

## ▶️ How to Run (Current Stage)

> At this stage, the CLI is scaffolded and runnable.

```bash
cd src
python -m word_counter.cli
```

Expected output:

```
Its a begining. And I won't stop here .....
```

---

## 📤 Output Formats (Planned)

* TXT report
* CSV report
* (Later) JSON / HTML

All outputs will be saved inside the `outputs/` directory.

---

## 🛠️ Tech Stack

* Python 3.14+
* CLI-based architecture
* Modular design (analyzers, exporters, utils)

---

## 🧭 Roadmap

* [ ] Project structure
* [ ] Runnable CLI scaffold
* [ ] Input handling (file path)
* [ ] TXT analyzer
* [ ] DOCX analyzer
* [ ] PDF analyzer
* [ ] CSV / TXT export
* [ ] Batch folder analysis
* [ ] Tests & validations

---

## 🎯 Learning Goals

This project helps practice:

* Python package structuring
* CLI application design
* File handling
* Modular, readable code
* Git & GitHub workflow

---

## ✨ Motivation

> *“It’s a beginning. And I won’t stop here …”*

This project is part of a **Beginner → Pro Python journey**.

---

##  License

MIT License 

