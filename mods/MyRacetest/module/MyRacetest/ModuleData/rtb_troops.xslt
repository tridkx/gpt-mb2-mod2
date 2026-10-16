<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="utf-8" indent="yes" />
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>
  <xsl:template match="NPCCharacter[@id='imperial_legionary']">
    <NPCCharacter id="imperial_legionary" default_group="Infantry" level="26" name="{{=JGsUtBT3}}Imperial Legionary" occupation="Soldier" culture="Culture.empire" race="yqs2_outfit2" is_female="true" face_mesh_cache="false">
      <face>
        <BodyProperties version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
        <BodyPropertiesMax version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
      </face>
		
		<skills>
			<skill id="Athletics" value="130" />
			<skill id="Riding" value="20" />
			<skill id="OneHanded" value="130" />
			<skill id="TwoHanded" value="80" />
			<skill id="Polearm" value="130" />
			<skill id="Bow" value="60" />
			<skill id="Crossbow" value="60" />
			<skill id="Throwing" value="80" />
		</skills>
		<upgrade_targets></upgrade_targets>
		
	<Equipments><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_sword_5_t4" /><equipment slot="Item1" id="Item.stronger_reinforced_kite_shield" /><equipment slot="Item2" id="Item.imperial_throwing_spear_1_t4" /><equipment slot="Item3" id="Item.imperial_throwing_spear_1_t4_2" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_mace_3_t4" /><equipment slot="Item1" id="Item.stronger_reinforced_kite_shield" /><equipment slot="Item2" id="Item.imperial_throwing_spear_1_t4" /><equipment slot="Item3" id="Item.imperial_throwing_spear_1_t4_2" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_mace_3_t4" /><equipment slot="Item1" id="Item.stronger_reinforced_kite_shield" /><equipment slot="Item2" id="Item.imperial_throwing_spear_1_t4" /><equipment slot="Item3" id="Item.imperial_throwing_spear_1_t4_2" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster></Equipments></NPCCharacter>
  </xsl:template>
  <xsl:template match="NPCCharacter[@id='imperial_elite_menavliaton']">
    <NPCCharacter id="imperial_elite_menavliaton" default_group="Infantry" level="26" name="{{=qAsnj7vU}}Imperial Elite Menavliaton" occupation="Soldier" culture="Culture.empire" race="yqs_default" is_female="true" face_mesh_cache="false">
      <face>
        <BodyProperties version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
        <BodyPropertiesMax version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
      </face>
		
		<skills>
			<skill id="Athletics" value="130" />
			<skill id="Riding" value="20" />
			<skill id="OneHanded" value="130" />
			<skill id="TwoHanded" value="80" />
			<skill id="Polearm" value="130" />
			<skill id="Bow" value="60" />
			<skill id="Crossbow" value="40" />
			<skill id="Throwing" value="80" />
		</skills>
		<upgrade_targets></upgrade_targets>
		
	<Equipments><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_polearm_1_t4" /><equipment slot="Item1" id="Item.empire_sword_4_t4" /><equipment slot="Item2" id="Item.imperial_throwing_spear_1_t4" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_polearm_1_t4" /><equipment slot="Item1" id="Item.empire_sword_4_t4" /><equipment slot="Item2" id="Item.imperial_throwing_spear_1_t4" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_polearm_1_t4" /><equipment slot="Item1" id="Item.empire_sword_4_t4" /><equipment slot="Item2" id="Item.imperial_throwing_spear_1_t4" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster></Equipments></NPCCharacter>
  </xsl:template>
  <xsl:template match="NPCCharacter[@id='imperial_palatine_guard']">
    <NPCCharacter id="imperial_palatine_guard" default_group="Ranged" level="26" name="{{=CDUvlu4d}}Imperial Palatine Guard" occupation="Soldier" culture="Culture.empire" race="bmq2_outfit2" is_female="true" face_mesh_cache="false">
      <face>
        <BodyProperties version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
        <BodyPropertiesMax version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
      </face>
		
		<skills>
			<skill id="Athletics" value="130" />
			<skill id="Riding" value="40" />
			<skill id="OneHanded" value="130" />
			<skill id="TwoHanded" value="30" />
			<skill id="Polearm" value="80" />
			<skill id="Bow" value="140" />
			<skill id="Crossbow" value="80" />
			<skill id="Throwing" value="60" />
		</skills>
		<upgrade_targets></upgrade_targets>
		
	<Equipments><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.steppe_war_bow" /><equipment slot="Item1" id="Item.bodkin_arrows_b" /><equipment slot="Item2" id="Item.bodkin_arrows_b" /><equipment slot="Item3" id="Item.empire_sword_3_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.steppe_war_bow" /><equipment slot="Item1" id="Item.bodkin_arrows_b" /><equipment slot="Item2" id="Item.bodkin_arrows_b" /><equipment slot="Item3" id="Item.empire_sword_3_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.steppe_war_bow" /><equipment slot="Item1" id="Item.bodkin_arrows_b" /><equipment slot="Item2" id="Item.bodkin_arrows_b" /><equipment slot="Item3" id="Item.empire_sword_3_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /></EquipmentRoster></Equipments></NPCCharacter>
  </xsl:template>
  <xsl:template match="NPCCharacter[@id='imperial_sergeant_crossbowman']">
    <NPCCharacter id="imperial_sergeant_crossbowman" default_group="Ranged" level="26" name="{{=THyv3q9f}}Imperial Sergeant Crossbowman" occupation="Soldier" culture="Culture.empire" race="bmq_default" is_female="true" face_mesh_cache="false">
      <face>
        <BodyProperties version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
        <BodyPropertiesMax version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
      </face>
		
		<skills>
			<skill id="Athletics" value="130" />
			<skill id="Riding" value="20" />
			<skill id="OneHanded" value="130" />
			<skill id="TwoHanded" value="60" />
			<skill id="Polearm" value="80" />
			<skill id="Bow" value="80" />
			<skill id="Crossbow" value="130" />
			<skill id="Throwing" value="60" />
		</skills>
		<upgrade_targets></upgrade_targets>
		
	<Equipments><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.crossbow_d" /><equipment slot="Item1" id="Item.bolt_d" /><equipment slot="Item2" id="Item.empire_mace_2_t4" /><equipment slot="Item3" id="Item.reinforced_kite_shield" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.crossbow_d" /><equipment slot="Item1" id="Item.bolt_d" /><equipment slot="Item2" id="Item.empire_sword_5_t4" /><equipment slot="Item3" id="Item.reinforced_kite_shield" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.crossbow_d" /><equipment slot="Item1" id="Item.bolt_d" /><equipment slot="Item2" id="Item.empire_mace_2_t4" /><equipment slot="Item3" id="Item.western_kite_shield" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_1_t2" /><equipment slot="Item1" id="Item.studded_bound_kite_shield" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_1_t2" /></EquipmentRoster></Equipments></NPCCharacter>
  </xsl:template>
  <xsl:template match="NPCCharacter[@id='imperial_elite_cataphract']">
    <NPCCharacter id="imperial_elite_cataphract" default_group="Cavalry" level="31" name="{{=MYwUFMsz}}Imperial Elite Cataphract" occupation="Soldier" culture="Culture.empire" race="txt5pve" is_female="true" face_mesh_cache="false">
      <face>
        <BodyProperties version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
        <BodyPropertiesMax version="4" age="25" weight="0.5" build="0.5" key="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" />
      </face>
		
		<skills>
			<skill id="Athletics" value="60" />
			<skill id="Riding" value="200" />
			<skill id="OneHanded" value="200" />
			<skill id="TwoHanded" value="60" />
			<skill id="Polearm" value="260" />
			<skill id="Bow" value="60" />
			<skill id="Crossbow" value="25" />
			<skill id="Throwing" value="45" />
		</skills>
		
	<Equipments><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_lance_3_t5" /><equipment slot="Item1" id="Item.empire_mace_5_t5" /><equipment slot="Horse" id="Item.t3_empire_horse" /><equipment slot="HorseHarness" id="Item.imperial_scale_barding" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_lance_3_t5" /><equipment slot="Item1" id="Item.empire_mace_5_t5" /><equipment slot="Horse" id="Item.t3_empire_horse" /><equipment slot="HorseHarness" id="Item.imperial_scale_barding" /></EquipmentRoster><EquipmentRoster equipmentType="Battle"><equipment slot="Item0" id="Item.empire_lance_3_t5" /><equipment slot="Item1" id="Item.empire_mace_5_t5" /><equipment slot="Horse" id="Item.t3_empire_horse" /><equipment slot="HorseHarness" id="Item.imperial_scale_barding" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /><equipment slot="Horse" id="Item.t3_empire_horse" /><equipment slot="HorseHarness" id="Item.imperial_scale_barding" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /><equipment slot="Horse" id="Item.t3_empire_horse" /><equipment slot="HorseHarness" id="Item.imperial_scale_barding" /></EquipmentRoster><EquipmentRoster equipmentType="Civilian"><equipment slot="Item0" id="Item.empire_sword_2_t3" /><equipment slot="Horse" id="Item.t3_empire_horse" /><equipment slot="HorseHarness" id="Item.imperial_scale_barding" /></EquipmentRoster></Equipments></NPCCharacter>
  </xsl:template>
</xsl:stylesheet>