BEGIN { FS="|"; print "ProductId|ProductPrice|ProductDescription|ProductCategory|" }
NR > 1 && $3 ~ /nut/ && $4 !~ /^[ ]*"?snacks"?[ ]*$/  { print $0 }
