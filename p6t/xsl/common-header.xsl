<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:param name="identity"/>
  <xsl:param name="secret"/>
  <xsl:param name="python"/>
  <xsl:param name="deployment_mode"/>
  <xsl:param name="operation"/>

  <xsl:variable name="operation_var">
    <xsl:choose>
      <xsl:when test="$operation"><xsl:value-of select="$operation"/></xsl:when>
      <xsl:when test="//PunchOutSetupRequest/@operation"><xsl:value-of select="//PunchOutSetupRequest/@operation"/></xsl:when>
      <xsl:otherwise>create</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="deployment_mode_var">
    <xsl:choose>
      <xsl:when test="$deployment_mode"><xsl:value-of select="$deployment_mode"/></xsl:when>
      <xsl:when test="//Request/@deploymentMode"><xsl:value-of select="//Request/@deploymentMode"/></xsl:when>
      <xsl:otherwise>test</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

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
