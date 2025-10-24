# Migration Guide - New Directory Structure

## 📂 What Changed

The codebase has been reorganized for better maintainability and scalability.

### Old Structure → New Structure

```
OLD:                                    NEW:
├── script.py                          ├── src/
├── another_script.py                  │   ├── script.py
├── resources.csv                      │   └── utils/
├── output.xlsx                        │       └── helper.py
└── docs/                              ├── data/
    └── README.md                      │   ├── input/
                                       │   │   └── resources.csv
                                       │   └── output/
                                       │       └── output.xlsx
                                       ├── docs/
                                       ├── tests/
                                       ├── config/
                                       └── run.py (NEW!)
```

## 🔄 Command Changes

### Before
```bash
python batch_enrich_pipeline_parallel.py --input resources.csv --workers 5
python categorize_resources.py --input enriched.xlsx
python filter_neurodivergent.py --input enriched.xlsx --filter
```

### After
```bash
python run.py enrich --input data/input/resources.csv --workers 5
python run.py categorize --input data/output/enriched.xlsx
python run.py filter --input data/output/enriched.xlsx --filter
```

## 📍 Default Path Changes

### Input Files
- **Old**: `to_be_normalised/enriched_resources.csv`
- **New**: `data/input/to_be_normalised/enriched_resources.csv`

### Output Files
- **Old**: `enriched_resources_parallel_*.xlsx` (current directory)
- **New**: `data/output/enriched_resources_parallel_*.xlsx`

### Cache
- **Unchanged**: `.cache/llm_extractions/`

## 🚀 Quick Start with New Structure

### 1. Place your input files
```bash
cp your_data.csv data/input/to_be_normalised/enriched_resources.csv
```

### 2. Run enrichment
```bash
python run.py enrich --workers 5 --rate-limit 15
```

### 3. Find output
```bash
ls data/output/enriched_resources_parallel_*.xlsx
```

## 🛠️ Script Locations

| Script | Old Location | New Location |
|--------|-------------|--------------|
| Main Pipeline (Parallel) | `batch_enrich_pipeline_parallel.py` | `src/batch_enrich_pipeline_parallel.py` |
| Main Pipeline (Sequential) | `batch_enrich_pipeline.py` | `src/batch_enrich_pipeline.py` |
| Web Extractor | `web_llm_extract.py` | `src/web_llm_extract.py` |
| Categorization | `categorize_resources.py` | `src/categorize_resources.py` |
| URL Population | `populate_gmaps_url.py` | `src/populate_gmaps_url.py` |
| Filter | `filter_neurodivergent.py` | `src/filter_neurodivergent.py` |
| Google Enrich | `enrich_with_google.py` | `src/utils/enrich_with_google.py` |
| Tests | `test_*.py` | `tests/test_*.py` |

## ⚙️ Configuration Files

| File | Old Location | New Location |
|------|-------------|--------------|
| Environment | `.env` | `.env` (unchanged) |
| Setup Script | `setup_env.sh` | `config/setup_env.sh` |
| Test Script | `test_pipeline.sh` | `config/test_pipeline.sh` |
| Dependencies | `pyproject.toml` | `pyproject.toml` (unchanged) |

## 📊 Benefits of New Structure

### ✅ Cleaner Root Directory
- Only essential files at root
- All code in `src/`
- All data in `data/`

### ✅ Better Organization
- Source code separated from data
- Tests in dedicated directory
- Documentation centralized

### ✅ Easier Navigation
- Logical grouping of related files
- Clear separation of concerns
- Easier to find specific functionality

### ✅ Scalability
- Easy to add new scripts to `src/`
- Simple to add new data sources to `data/input/`
- Clean separation for version control

## 🔧 Backwards Compatibility

### If you have existing scripts that reference old paths:

1. **Update hardcoded paths:**
   ```python
   # Old
   input_file = "to_be_normalised/enriched_resources.csv"
   
   # New
   input_file = "data/input/to_be_normalised/enriched_resources.csv"
   ```

2. **Use the new CLI:**
   ```bash
   python run.py <command> [options]
   ```

3. **Or call scripts directly:**
   ```bash
   python src/batch_enrich_pipeline_parallel.py --input data/input/file.csv
   ```

## 📝 Import Changes

If you're importing modules in custom scripts:

```python
# Old (if scripts were in root)
from batch_enrich_pipeline_parallel import categorize_resource

# New (from root directory)
from src.batch_enrich_pipeline_parallel import categorize_resource

# Or from within src/
from .batch_enrich_pipeline_parallel import categorize_resource
```

## 🎯 Next Steps

1. ✅ Review new structure
2. ✅ Update your scripts to use new paths
3. ✅ Test with `python run.py enrich --help`
4. ✅ Move your data files to `data/input/`
5. ✅ Check output in `data/output/`

## ❓ Questions?

- See [README.md](README.md) for full documentation
- Check [docs/START_HERE.md](docs/START_HERE.md) for quick start
- Review [docs/SETUP.md](docs/SETUP.md) for setup instructions

---

**Migration completed! 🎉** Your workflow is now cleaner and more maintainable.

