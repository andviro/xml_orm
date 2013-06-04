<?xml version="1.0"?>
<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xsl:output method="text" encoding="utf-8"/>

    <xsl:template match="/">
        <xsl:apply-templates select="*" mode="class"/>
    </xsl:template>

    <xsl:template match="*" mode="class">
        <xsl:apply-templates select="*" mode="class"/>
class Element(core.Schema):
    class Meta:
        root = u'<xsl:value-of select="local-name()"/>'
        <xsl:apply-templates select="*" mode="fields"/>
        <xsl:apply-templates select="@*"/>
    </xsl:template>

    <xsl:template match="*" mode="fields">
        <xsl:choose>
            <xsl:when test="* or @*">
    #<xsl:value-of select="local-name()"/>
    field = core.ComplexField(Element)
            </xsl:when>
            <xsl:otherwise>
    field = core.SimpleField(u'<xsl:value-of select="local-name()"/>')
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="@*">
    field = core.SimpleField(u'@<xsl:value-of select="local-name()"/>')
    </xsl:template>

</xsl:stylesheet>

