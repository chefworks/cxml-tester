<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:template match="ItemIn">
    <ItemOut quantity="{@quantity}">
      <xsl:apply-templates/>
    </ItemOut>
  </xsl:template>

</xsl:stylesheet>
