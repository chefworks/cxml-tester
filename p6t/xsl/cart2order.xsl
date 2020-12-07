<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:import href="copyover.xsl"/>
  <xsl:import href="common-header.xsl"/>
  <xsl:import href="item-out.xsl"/>

  <xsl:output method="xml" indent="yes" encoding="utf-8"/>

  <xsl:strip-space elements="*"/>
  
  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="PunchOutOrderMessageHeader">
    <OrderRequestHeader orderID="85PO0000219" orderDate="2016-04-12T10:35:27">
      <xsl:apply-templates select="Total|ShipTo|Shipping|Tax"/>
    </OrderRequestHeader>
  </xsl:template>
  
  <xsl:template match="Message">
    <Request deploymentMode="{$deployment_mode_var}">
      <OrderRequest>
        <xsl:apply-templates select="PunchOutOrderMessage/PunchOutOrderMessageHeader"/>
        <xsl:apply-templates select="PunchOutOrderMessage/ItemIn"/>
      </OrderRequest>
    </Request>
  </xsl:template>

</xsl:stylesheet>
