"""
Update API with the latest best model
"""

import os
import json
import shutil
from pathlib import Path

def update_api_model():
    """Update the API to use the latest best model"""
    
    print("="*80)
    print("  UPDATING API WITH LATEST BEST MODEL")
    print("="*80 + "\n")
    
    # Find the latest model
    model_dir = Path("models/katib")
    model_files = list(model_dir.glob("*.pkl"))
    
    if not model_files:
        print("❌ No models found in models/katib/")
        return False
    
    # Sort by modification time
    latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
    
    print(f"📦 Latest model: {latest_model.name}")
    
    # Check for metrics file
    metrics_file = latest_model.with_name(latest_model.stem + '_metrics.json')
    
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        print(f"   Accuracy:  {metrics.get('accuracy', 0):.4f}")
        print(f"   Precision: {metrics.get('precision', 0):.4f}")
        print(f"   Recall:    {metrics.get('recall', 0):.4f}")
        print(f"   F1 Score:  {metrics.get('f1', 0):.4f}")
    
    # Copy to main models directory
    dest_model = Path("models") / "best_model.pkl"
    dest_metrics = Path("models") / "best_model_metrics.json"
    
    print(f"\n📋 Copying to: {dest_model}")
    shutil.copy2(latest_model, dest_model)
    
    if metrics_file.exists():
        print(f"📋 Copying metrics to: {dest_metrics}")
        shutil.copy2(metrics_file, dest_metrics)
    
    # Update model info file
    model_info = {
        "model_path": str(dest_model),
        "source_model": str(latest_model),
        "metrics": metrics if metrics_file.exists() else {},
        "updated_at": Path(latest_model).stat().st_mtime
    }
    
    info_file = Path("models") / "model_info.json"
    with open(info_file, 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"📋 Model info saved to: {info_file}")
    
    print("\n" + "="*80)
    print("✅ API MODEL UPDATED SUCCESSFULLY!")
    print("="*80)
    print("\n⚠️  Please restart the FastAPI server:")
    print("   1. Stop current server (Ctrl+C)")
    print("   2. Run: python src/deployment/api_fastapi.py")
    print("\nOr the server will auto-reload if running with --reload flag")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    update_api_model()
