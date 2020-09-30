<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:param name="identity"/>
  <xsl:param name="secret"/>
  <xsl:param name="python"/>

  <xsl:template match="From/Credential/Identity/text()">
    <xsl:choose>
      <xsl:when test="$identity">
        <xsl:value-of select="$identity"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="."/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="Sender/Credential">
    <xsl:copy>
      <xsl:apply-templates select="*[name() != 'SharedSecret']|@*|text()"/>
      <xsl:choose>
        <xsl:when test="$secret">
          <SharedSecret><xsl:value-of select="$secret"/></SharedSecret>
        </xsl:when>
        <xsl:when test="SharedSecret">
          <xsl:copy-of select="SharedSecret"/>
        </xsl:when>
        <xsl:otherwise>
          <SharedSecret>1234</SharedSecret>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
