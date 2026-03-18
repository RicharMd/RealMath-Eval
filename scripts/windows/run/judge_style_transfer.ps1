# PowerShell Script - RealMath-Eval Style Transfer Inference
# Using Gemini 3 Flash Preview model with CoT method

# Set UTF-8 encoding for Python
param(
    [string]$dataset_name = "realmath_eval_style_transfer",  # data file: data/${dataset_name}.json
    [string]$output_bucket = "realmath_eval",                     # output path: outputs/${output_bucket}/...
    [string]$method = "cot",
    [string]$model = "gemini-3-flash-preview"
)


$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# Configuration

# Generate timestamp for unique output directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Paths
$output_dir = "./outputs/${output_bucket}/${method}/${model}/${timestamp}"
$log_file = "${output_dir}/inference.log"

# Create output directory
if (!(Test-Path $output_dir)) {
    New-Item -ItemType Directory -Path $output_dir -Force | Out-Null
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "RealMath-Eval Style Transfer $dataset_name  <->  $method $model Inference" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Dataset: $dataset_name" -ForegroundColor Yellow
Write-Host "Method: $method" -ForegroundColor Yellow
Write-Host "Model: $model" -ForegroundColor Yellow
Write-Host "Output directory: $output_dir" -ForegroundColor Yellow
Write-Host "Log file: $log_file" -ForegroundColor Yellow
Write-Host ""

# Run inference
Write-Host "Starting inference..." -ForegroundColor Cyan
try {
    $arguments = @(
        "inference.py",
        "--test_dataset_name", $dataset_name,
        "--method_name", $method,
        "--model_name", $model,
        "--output_path", "${output_dir}/results.jsonl",
        "--model_temperature", "0.7",
        "--model_max_tokens", "30000",
        "--model_timeout", "600"
    )
    
    # Run Python script and output to both console and log file
    python $arguments 2>&1 | Tee-Object -FilePath $log_file
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Inference completed!" -ForegroundColor Green
        Write-Host "Results saved to: $output_dir" -ForegroundColor Green
        Write-Host "Log saved to: $log_file" -ForegroundColor Green
    } else {
        Write-Host "Inference failed!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host "Error: Inference execution failed - $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Auto-extract rewritten responses
$results_file = "${output_dir}/results.jsonl"
if (Test-Path $results_file) {
    Write-Host ""
    Write-Host "=== Starting Response Extraction ===" -ForegroundColor Green

    try {
        python eval/extract_style_transfer_response.py `
            --input-file "$results_file" `
            --output-file "${output_dir}/results_extracted_rewritten.jsonl"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Response extraction completed!" -ForegroundColor Green
        } else {
            Write-Host "Response extraction failed!" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error: Response extraction execution failed - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "=== Quick Summary ===" -ForegroundColor Green
    
    try {
        # Read results file and show summary
        $results = @()
        Get-Content $results_file | ForEach-Object {
            if ($_.Trim()) {
                $results += ($_ | ConvertFrom-Json)
            }
        }
        
        Write-Host "Total samples processed: $($results.Count)" -ForegroundColor Yellow
        
        if ($results.Count -gt 0) {
            $sample = $results[0]
            Write-Host "Sample GT: $($sample.gt)" -ForegroundColor Yellow
            $responsePreview = $sample.response
            if ($responsePreview.Length -gt 150) {
                $responsePreview = $responsePreview.Substring(0, 150) + "..."
            }
            Write-Host "Sample response preview: $responsePreview" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Error: Cannot read results file - $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "Warning: Results file not found at $results_file" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Script execution completed!" -ForegroundColor Green
Read-Host "Press Enter to exit"
