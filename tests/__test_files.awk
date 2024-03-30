BEGIN { FS="|"; print "ProductId|ProductPrice|ProductDescription|ProductCategory|" }
NR > 1 && !($1 ~ /^(1123|1128|1129) $/ || $3 ~ /crumpets/)  { print $0 }
