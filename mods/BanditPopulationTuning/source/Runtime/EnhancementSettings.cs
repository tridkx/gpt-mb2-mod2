using MCM.Abstractions.Attributes;
using MCM.Abstractions.Attributes.v2;

namespace BanditPopulationTuning
{
    public sealed partial class Settings
    {
        [SettingPropertyFloatingInteger("AI领主带兵上限倍率", 0.25f, 5f, "0.00", Order = 0, RequireRestart = false,
            HintText = "最终上限=原计算结果×此倍率+额外人数，向下取整。默认1，不抹去等级、技能、特长等差异；排除玩家家族、商队、驻军、民兵和土匪。")]
        [SettingPropertyGroup("AI家族与带兵", GroupOrder = 1)]
        public float AIPartySizeMultiplier { get; set; } = 1f;

        [SettingPropertyInteger("AI领主带兵上限额外人数", 0, 1000, Order = 1, RequireRestart = false,
            HintText = "默认0，独立加在倍率之后。改变容量，不立即填满队伍；不影响玩家家族。")]
        [SettingPropertyGroup("AI家族与带兵", GroupOrder = 1)]
        public int AIPartySizeBonus { get; set; }

        [SettingPropertyInteger("AI家族额外队伍名额", 0, 20, Order = 2, RequireRestart = false,
            HintText = "默认0。在原版计算的家族队伍上限上相加，不统一设为固定值；排除玩家家族、土匪和已消亡家族。不强制创建队伍。")]
        [SettingPropertyGroup("AI家族与带兵", GroupOrder = 1)]
        public int AIClanPartyBonus { get; set; }

        [SettingPropertyInteger("每名士兵每日额外经验", 0, 10000, Order = 0, RequireRestart = false,
            HintText = "默认0。每组增加=本组人数×此值，每天一次；包括伤员，排除英雄、俘虏和无升级目标的终点兵。仅非玩家家族的正常AI领主队伍。")]
        [SettingPropertyGroup("AI队伍每日补充", GroupOrder = 2)]
        public int AIDailyExperiencePerSoldier { get; set; }

        [SettingPropertyInteger("每日额外普通新兵", 0, 100, Order = 1, RequireRestart = false,
            HintText = "默认0。按领主文化补充基础普通兵，遵守剩余容量；与贵族兵轮流分配名额。不直接补高级兵，不在进行中战斗内补充。")]
        [SettingPropertyGroup("AI队伍每日补充", GroupOrder = 2)]
        public int AIDailyBasicTroops { get; set; }

        [SettingPropertyInteger("每日额外贵族新兵", 0, 100, Order = 2, RequireRestart = false,
            HintText = "默认0。使用领主文化的贵族线基础兵，与普通兵共享剩余容量；缺少该文化入口时跳过该类。")]
        [SettingPropertyGroup("AI队伍每日补充", GroupOrder = 2)]
        public int AIDailyEliteTroops { get; set; }

        [SettingPropertyFloatingInteger("每日每7人额外谷物", 0f, 10f, "0.00", Order = 3, RequireRestart = false,
            HintText = "默认0。按实际队伍成员人数计算，小数跨日累计；库存按全部食物计算上限，不无限囤粮。不含俘虏。")]
        [SettingPropertyGroup("AI队伍每日补充", GroupOrder = 2)]
        public float AIDailyGrainPerSeven { get; set; }

        [SettingPropertyInteger("补粮库存上限（天）", 1, 30, Order = 4, RequireRestart = false,
            HintText = "默认10。仅限制本功能额外发放，按当前每日实际食物消耗计算；达到上限停止发粮，不删除已有库存，不积压未发粮食。")]
        [SettingPropertyGroup("AI队伍每日补充", GroupOrder = 2)]
        public int GrainStockDays { get; set; } = 10;

        [SettingPropertyInteger("AI领主每周额外第纳尔", 0, 100000, Order = 0, RequireRestart = false,
            HintText = "默认0。每七天给存活且未被俘的非玩家家族领主增加一次；不影响玩家、同伴或其他玩家家族成员。")]
        [SettingPropertyGroup("AI领主每周补充", GroupOrder = 3)]
        public int AILordWeeklyGold { get; set; }

        [SettingPropertyInteger("AI领主每周各技能额外经验", 0, 10000, Order = 1, RequireRestart = false,
            HintText = "默认0。对18项原版技能分别提供经验，继续经过原版技能学习机制；不是直接增加技能等级。")]
        [SettingPropertyGroup("AI领主每周补充", GroupOrder = 3)]
        public int AILordWeeklySkillXp { get; set; }

        [SettingPropertyBool("定居点增量仅影响非玩家家族", Order = 0, RequireRestart = false,
            HintText = "默认开启。关闭后也作用于玩家家族城镇／城堡。下方所有增量默认0；不处理村庄，与村庄民兵Mod分开。")]
        [SettingPropertyGroup("城镇与城堡", GroupOrder = 4)]
        public bool SettlementAIOnly { get; set; } = true;

        [SettingPropertyFloatingInteger("每日忠诚额外增量", 0f, 100f, "0.00", Order = 1, RequireRestart = false)]
        [SettingPropertyGroup("城镇与城堡", GroupOrder = 4)]
        public float SettlementLoyaltyBonus { get; set; }
        [SettingPropertyFloatingInteger("每日食物额外增量", 0f, 100f, "0.00", Order = 2, RequireRestart = false)]
        [SettingPropertyGroup("城镇与城堡", GroupOrder = 4)]
        public float SettlementFoodBonus { get; set; }
        [SettingPropertyFloatingInteger("每日民兵额外增量", 0f, 100f, "0.00", Order = 3, RequireRestart = false,
            HintText = "默认0，只增加城镇／城堡每日民兵增长；村庄保持现有村庄民兵Mod的规则。")]
        [SettingPropertyGroup("城镇与城堡", GroupOrder = 4)]
        public float SettlementMilitiaBonus { get; set; }
        [SettingPropertyFloatingInteger("每日繁荣额外增量", 0f, 100f, "0.00", Order = 4, RequireRestart = false)]
        [SettingPropertyGroup("城镇与城堡", GroupOrder = 4)]
        public float SettlementProsperityBonus { get; set; }
        [SettingPropertyFloatingInteger("每日治安额外增量", 0f, 100f, "0.00", Order = 5, RequireRestart = false)]
        [SettingPropertyGroup("城镇与城堡", GroupOrder = 4)]
        public float SettlementSecurityBonus { get; set; }
        [SettingPropertyInteger("每日税收额外第纳尔", 0, 10000, Order = 6, RequireRestart = false)]
        [SettingPropertyGroup("城镇与城堡", GroupOrder = 4)]
        public int SettlementTaxBonus { get; set; }

        [SettingPropertyInteger("其他英雄额外生命", 0, 5000, Order = 0, RequireRestart = false,
            HintText = "默认0。除玩家主角外的所有英雄，包括同伴；普通士兵不变。只增加最大生命，不立即治疗。")]
        [SettingPropertyGroup("英雄战斗", GroupOrder = 5)]
        public int OtherHeroHealthBonus { get; set; }
        [SettingPropertyInteger("玩家额外生命", 0, 5000, Order = 1, RequireRestart = false)]
        [SettingPropertyGroup("英雄战斗", GroupOrder = 5)]
        public int PlayerHealthBonus { get; set; }
        [SettingPropertyFloatingInteger("其他英雄额外伤害（%）", 0f, 500f, "0.00", Order = 2, RequireRestart = false,
            HintText = "默认0。除玩家主角外的英雄在实际战役战斗中造成的伤害乘以(1+此值/100)。不改变自动战斗，不影响普通士兵。")]
        [SettingPropertyGroup("英雄战斗", GroupOrder = 5)]
        public float OtherHeroDamagePercent { get; set; }
        [SettingPropertyFloatingInteger("玩家额外伤害（%）", 0f, 500f, "0.00", Order = 3, RequireRestart = false)]
        [SettingPropertyGroup("英雄战斗", GroupOrder = 5)]
        public float PlayerDamagePercent { get; set; }
    }
}
