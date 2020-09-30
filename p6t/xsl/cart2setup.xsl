<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:import href="copyover.xsl"/>
  <xsl:import href="common-header.xsl"/>
  <xsl:import href="item-out.xsl"/>

  <xsl:param name="deployment_mode">test</xsl:param>
  <xsl:param name="operation">create</xsl:param>
  <xsl:param name="buyer_cookie">6e074e0c-02e6-11eb-988e-1321f6d6b14f</xsl:param>
  <xsl:param name="python"/>

  <xsl:output method="xml" indent="yes" encoding="utf-8"/>

  <xsl:strip-space elements="*"/>

  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="Message">
    <Request deploymentMode="{$deployment_mode}">
      <PunchOutSetupRequest operation="{$operation}">
        <xsl:apply-templates select="PunchOutOrderMessage/BuyerCookie"/>
        <BrowserFormPost>
          <URL>https://example.com/punchout-cart-return/bababuba</URL>
        </BrowserFormPost>
        <xsl:apply-templates select="PunchOutOrderMessage/PunchOutOrderMessageHeader/ShipTo"/>
        <xsl:apply-templates select="PunchOutOrderMessage/ItemIn"/>
      </PunchOutSetupRequest>
    </Request>
  </xsl:template>

</xsl:stylesheet>
