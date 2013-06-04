<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xsl:output method="text" encoding="utf-8"/>

    <xml:strip-space elements="*"/>

    <xsl:template match="/xs:schema">
        <xsl:text>
# coding: utf-8
        </xsl:text>
        <xsl:apply-templates select="." mode="class"/>
    </xsl:template>


    <xsl:template match="xs:element" mode="class">
        <xsl:param name="suffix" default="_"/>
        <xsl:param name="tab" default="    "/>
class Element<xsl:value-of select="$suffix"/>_<xsl:value-of select="position()"/>(core.Schema):
    u'''<xsl:value-of select="normalize-space(xs:annotation)"/>'''
        <xsl:apply-templates mode="inline" select="xs:complexType/*">
            <xsl:with-param name="suffix" select="concat($suffix, position())"/>
            <xsl:with-param name="tab" select="concat($tab, '    ')"/>
        </xsl:apply-templates>
    class Meta:
        root = u'<xsl:value-of select="@name"/>'
    </xsl:template>


    <xsl:template match="xs:element" mode="inline">
        <xsl:param name="suffix" default="_"/>
        <xsl:param name="tab" default="    "/>
<xsl:value-of select="$tab"/>field<xsl:value-of select="concat($suffix, position())"/> = <xsl:choose>
    <xsl:when test="xs:complexType">
ComplexField('<xsl:value-of select="@name"/>',
<xsl:apply-templates mode="inline">
    <xsl:with-param name="suffix" select="concat($suffix, position())"/>
    <xsl:with-param name="tab" select="concat($tab, '    ')"/>
</xsl:apply-templates>
)
    </xsl:when>
    <xsl:otherwise>
SimpleField('<xsl:value-of select="@name"/>')
    </xsl:otherwise>
</xsl:choose>
    </xsl:template>


    <xsl:template match="xs:attribute" mode="inline">
<xsl:param name="suffix" default="_"/>
<xsl:param name="tab" default="    "/>
<xsl:value-of select="$tab"/>field<xsl:value-of select="concat($suffix, position())"/> = core.SimpleField(u'@<xsl:value-of select="@name"/>')
    </xsl:template>


    <xsl:template match="xs:sequence" mode="inline">
        <xsl:param name="suffix" default="_"/>
        <xsl:param name="tab" default="    "/>
        <xsl:apply-templates mode="inline">
            <xsl:with-param name="suffix" select="$suffix"/>
            <xsl:with-param name="tab" select="$tab"/>
        </xsl:apply-templates>
    </xsl:template>


    <xsl:template match="xs:choice" mode="inline">
        <xsl:param name="suffix" default="_"/>
        <xsl:param name="tab" default="    "/>
        <xsl:apply-templates mode="inline">
    <xsl:with-param name="suffix" select="concat($suffix, position())"/>
    <xsl:with-param name="tab" select="concat($tab, '    ')"/>
        </xsl:apply-templates>
    </xsl:template>
</xsl:stylesheet>

