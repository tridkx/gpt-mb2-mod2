<?xml version='1.0' encoding='utf-8'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" encoding="utf-8" indent="yes" />
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>
  <xsl:template match="NPCCharacter[@id='imperial_vigla_recruit']">
    <NPCCharacter id="imperial_vigla_recruit" default_group="Infantry" level="11" name="月清疏贵族新兵" occupation="Soldier" is_basic_troop="true" culture="Culture.empire" race="yqs_default" is_female="true" age="25" face_mesh_cache="false">
      <face>
        <BodyProperties version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
        <BodyPropertiesMax version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
      </face>
      <skills>
        <skill id="Athletics" value="20" />
        <skill id="Riding" value="40" />
        <skill id="OneHanded" value="60" />
        <skill id="TwoHanded" value="5" />
        <skill id="Polearm" value="40" />
        <skill id="Bow" value="20" />
        <skill id="Crossbow" value="5" />
        <skill id="Throwing" value="5" />
      </skills>
      <upgrade_targets>
        <upgrade_target id="NPCCharacter.imperial_equite" />
      </upgrade_targets>
      <Equipments>
        <EquipmentRoster>
          <equipment slot="Item0" id="Item.western_spear_2_t2" />
          <equipment slot="Item1" id="Item.reinforced_flat_kite_shield" />
          <equipment slot="Item2" id="Item.empire_sword_1_t2" />
        </EquipmentRoster>
        <EquipmentRoster>
          <equipment slot="Item0" id="Item.western_spear_2_t2" />
          <equipment slot="Item1" id="Item.reinforced_flat_kite_shield" />
          <equipment slot="Item2" id="Item.empire_sword_1_t2" />
        </EquipmentRoster>
        <EquipmentRoster>
          <equipment slot="Item0" id="Item.western_spear_2_t2" />
          <equipment slot="Item1" id="Item.reinforced_flat_kite_shield" />
          <equipment slot="Item2" id="Item.empire_sword_1_t2" />
        </EquipmentRoster>
        <EquipmentRoster equipmentType="Civilian" />
      </Equipments>
    </NPCCharacter>
  </xsl:template>
</xsl:stylesheet>