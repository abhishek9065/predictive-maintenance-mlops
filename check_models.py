"""
Check and verify model files
"""

import pickle
import os

def check_all_models():
    """Check all model files"""
    model_dir = 'models'
    
    print("="*80)
    print("  CHECKING ALL MODEL FILES")
    print("="*80 + "\n")
    
    model_files = [
        'best_model.pkl',
        'production_model.pkl',
        'quick_model.pkl',
        'staging_model.pkl'
    ]
    
    for model_file in model_files:
        filepath = os.path.join(model_dir, model_file)
        
        if not os.path.exists(filepath):
            print(f"❌ {model_file}: NOT FOUND")
            continue
        
        file_size = os.path.getsize(filepath)
        print(f"\n📦 {model_file}:")
        print(f"   Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        try:
            with open(filepath, 'rb') as f:
                # Try to read first few bytes
                first_bytes = f.read(10)
                print(f"   First bytes: {first_bytes[:10]}")
                
                # Reset and try to load
                f.seek(0)
                model = pickle.load(f)
                
                print(f"   ✅ Model loaded successfully")
                print(f"   Type: {type(model).__name__}")
                
                if hasattr(model, 'n_estimators'):
                    print(f"   Estimators: {model.n_estimators}")
                if hasattr(model, 'n_features_in_'):
                    print(f"   Features: {model.n_features_in_}")
                
        except Exception as e:
            print(f"   ❌ Error loading: {str(e)[:100]}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    check_all_models()
