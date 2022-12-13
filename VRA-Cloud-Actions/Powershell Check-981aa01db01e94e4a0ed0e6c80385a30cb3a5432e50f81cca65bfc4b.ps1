function handler($context, $inputs) {
  Write-Host "Hello " $inputs.target

  return $inputs
}
