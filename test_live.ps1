$endpoints = @('/news/latest?limit=3', '/news/category/technology?limit=3', '/news/category/sports?limit=3')
foreach ($ep in $endpoints) {
    Write-Output "`n=== $ep ==="
    $res = Invoke-RestMethod -Uri "http://localhost:8000/api/v1$ep"
    foreach ($item in $res.items) {
        $r = $item.region
        $c = $item.category.name
        $t = $item.title
        $d = $item.is_demo
        Write-Output " - [$r | $c] $t (demo=$d)"
    }
}
