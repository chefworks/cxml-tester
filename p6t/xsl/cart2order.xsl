<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:param name="identity"/>
  <xsl:param name="secret"/>
  <xsl:param name="deployment_mode" select="'test'"/>
  <xsl:param name="python"/>

  <xsl:output method="xml" indent="yes" encoding="utf-8"/>

  <xsl:strip-space elements="*"/>
  
  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>

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
        <xsl:when test="$secret = 'null' or $secret = 'none' or $secret = 'delete'"/>
        <xsl:when test="$secret">
          <SharedSecret><xsl:value-of select="$secret"/></SharedSecret>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates select="SharedSecret"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="$secret">
      </xsl:if>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="PunchOutOrderMessageHeader">
    <OrderRequestHeader orderID="85PO0000219" orderDate="2016-04-12T10:35:27">
      <xsl:apply-templates select="Total|ShipTo|Shipping|Tax"/>
    </OrderRequestHeader>
  </xsl:template>
  
  <xsl:template match="Message">
    <Request deploymentMode="{$deployment_mode}">
      <OrderRequest>
        <xsl:apply-templates select="PunchOutOrderMessage/PunchOutOrderMessageHeader"/>
        <xsl:apply-templates select="PunchOutOrderMessage/ItemIn"/>
      </OrderRequest>
    </Request>
  </xsl:template>

  <xsl:template match="ItemIn">
    <ItemOut quantity="{@quantity}">
      <xsl:apply-templates/>
    </ItemOut>
  </xsl:template>
  
  <xsl:template match="@*|*|text()|processing-instruction()|comment()">
    <xsl:copy>
      <xsl:apply-templates select="@*|*|text()|processing-instruction()|comment()"/>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
