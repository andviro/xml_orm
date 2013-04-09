<?xml version="1.0"?>
<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xsl:output method="text" encoding="utf-8"/>

    <xsl:template match="/xs:schema">
        <xsl:apply-templates select="." mode="class"/>
    </xsl:template>

    <xsl:template match="xs:element" mode="class">
        <xsl:apply-templates select="xs:complexType/xs:sequence/xs:element"
            mode="class"/>
class Element(core.Schema):
    u'''<xsl:value-of select="normalize-space(xs:annotation)"/>'''
    class Meta:
        root = u'<xsl:value-of select="@name"/>'
        <xsl:apply-templates select="xs:complexType" mode="fields"/>
    </xsl:template>

    <xsl:template match="xs:element" mode="fields">
        <xsl:choose>
            <xsl:when test="xs:complexType">
    #<xsl:value-of select="@name"/>
    field = core.ComplexField(Element)
            </xsl:when>
            <xsl:otherwise>
    field = core.SimpleField(u'<xsl:value-of select="@name"/>')
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="xs:attribute">
    field = core.SimpleField(u'@<xsl:value-of select="@name"/>')
    </xsl:template>

    <xsl:template match="xs:complexType" mode="fields">
        <xsl:apply-templates select="xs:sequence/xs:element" mode="fields"/>
        <xsl:apply-templates select="xs:attribute" />
    </xsl:template>
</xsl:stylesheet>

