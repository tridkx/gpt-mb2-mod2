<?xml version='1.0' encoding='utf-8'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" encoding="utf-8" indent="yes" />
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>
  <xsl:template match="NPCCharacter[@id='imperial_recruit']">
    <NPCCharacter id="imperial_recruit" default_group="Infantry" level="6" name="五毒苍蓝新兵" occupation="Soldier" is_basic_troop="true" culture="Culture.empire" race="wdr_canglan" is_female="true" age="25" face_mesh_cache="false">
      <face>
        <BodyProperties version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
        <BodyPropertiesMax version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
      </face>
      <skills>
        <skill id="Athletics" value="20" />
        <skill id="Riding" value="0" />
        <skill id="OneHanded" value="20" />
        <skill id="TwoHanded" value="10" />
        <skill id="Polearm" value="20" />
        <skill id="Bow" value="5" />
        <skill id="Crossbow" value="5" />
        <skill id="Throwing" value="10" />
      </skills>
      <upgrade_targets>
        <upgrade_target id="NPCCharacter.imperial_infantryman" />
        <upgrade_target id="NPCCharacter.imperial_archer" />
      </upgrade_targets>
      <Equipments>
        <EquipmentRoster>
          <equipment slot="Item0" id="Item.peasant_pitchfork_2_t1" />
        </EquipmentRoster>
        <EquipmentRoster>
          <equipment slot="Item0" id="Item.peasant_polearm_1_t1" />
        </EquipmentRoster>
        <EquipmentRoster>
          <equipment slot="Item0" id="Item.peasant_sickle_1_t1" />
        </EquipmentRoster>
        <EquipmentRoster>
          <equipment slot="Item0" id="Item.empire_sword_1_t2" />
        </EquipmentRoster>
        <EquipmentRoster equipmentType="Civilian" />
      </Equipments>
    </NPCCharacter>
  </xsl:template>
</xsl:stylesheet>