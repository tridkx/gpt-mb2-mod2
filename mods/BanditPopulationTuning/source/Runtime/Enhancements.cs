using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;
using TaleWorlds.CampaignSystem;
using TaleWorlds.CampaignSystem.GameComponents;
using TaleWorlds.CampaignSystem.Party;
using TaleWorlds.CampaignSystem.Settlements;
using TaleWorlds.Localization;
using TaleWorlds.MountAndBlade;

namespace BanditPopulationTuning
{
    public static class EnhancementRules
    {
        public static int SafeInt(int value, int max) => Math.Max(0, Math.Min(max, value));
        public static bool EligibleClan(bool exists, bool playerClan, bool bandit, bool eliminated) => exists && !playerClan && !bandit && !eliminated;
        public static bool EligibleParty(bool eligibleClan, bool lordParty, bool active, bool disbanding, bool leaderAlive, bool prisoner, bool playerParty) =>
            eligibleClan && lordParty && active && !disbanding && leaderAlive && !prisoner && !playerParty;
        public static bool AIClan(Clan clan) => clan != null && EnhancementRules.EligibleClan(true, clan == Clan.PlayerClan, clan.IsBanditFaction, clan.IsEliminated);
        public static bool AIParty(MobileParty party) => party != null && EligibleParty(AIClan(party.ActualClan), party.IsLordParty,
            party.IsActive, party.IsDisbanding, party.LeaderHero != null && party.LeaderHero.IsAlive,
            party.LeaderHero?.IsPrisoner ?? true, party == MobileParty.MainParty);
        public static bool Settlement(bool fortification, bool playerClan, bool aiOnly) => fortification && (!aiOnly || !playerClan);
        public static bool Settlement(Settlement settlement) => settlement != null && settlement.OwnerClan != null &&
            Settlement(settlement.IsTown || settlement.IsCastle, settlement.OwnerClan == Clan.PlayerClan, Settings.Current.SettlementAIOnly);
        public static float PartyCapacity(float baseline, float multiplier, int bonus) => Math.Max(1f,
            (float)Math.Floor(baseline * Rules.Safe(multiplier, .25f, 5f, 1f) + SafeInt(bonus, 1000)));
        public static int ClanCapacity(int baseline, int bonus) => (int)Math.Min(int.MaxValue, (long)baseline + SafeInt(bonus, 20));
        public static float HeroDamage(float baseline, bool hero, bool player, Settings s) => !hero || baseline <= 0 ? baseline :
            baseline * (1f + Rules.Safe(player ? s.PlayerDamagePercent : s.OtherHeroDamagePercent, 0f, 500f, 0f) / 100f);
        public static int Experience(int count, int perSoldier, int existing, bool canUpgrade) => !canUpgrade ? 0 :
            (int)Math.Max(0L, Math.Min((long)Math.Max(0, count) * SafeInt(perSoldier,10000), (long)int.MaxValue - Math.Max(0,existing)));
        public static int[] Recruitment(int members, int capacity, int basic, int elite, bool hasBasic, bool hasElite)
        {
            int room=Math.Max(0,capacity-members), a=0,b=0;
            basic=hasBasic ? SafeInt(basic,100) : 0; elite=hasElite ? SafeInt(elite,100) : 0;
            while(room>0 && (a<basic || b<elite))
            {
                if(a<basic && room>0) {a++;room--;}
                if(b<elite && room>0) {b++;room--;}
            }
            return new[]{a,b};
        }
        public static int Grain(int members, float perSeven, float carry, float food, float dailyConsumption, int days, out float nextCarry)
        {
            nextCarry=0;
            if (members<=0 || perSeven<=0 || dailyConsumption<=0) return 0;
            double stockLimit=Math.Ceiling(dailyConsumption * Math.Max(1,Math.Min(30,days)));
            int room=(int)Math.Max(0,Math.Min(int.MaxValue,Math.Floor(stockLimit-Math.Max(0,food))));
            if(room==0) return 0;
            double desired=members*Rules.Safe(perSeven,0f,10f,0f)/7.0+Rules.Safe(carry,0f,.999999f,0f);
            int whole=(int)Math.Floor(desired);
            int amount=Math.Min(whole,room);
            nextCarry=amount==room ? 0 : (float)(desired-whole);
            return amount;
        }
        // Flatten native factors only when changing the final value. Preserve all native UI lines.
        public static void AddFinal(ref ExplainedNumber number,float delta,string label)
        {
            if (delta==0) return;
            var updated=new ExplainedNumber(0f,number.IncludeDescriptions);
            updated.AddFromExplainedNumber(number,new TextObject("原计算结果"));
            updated.Add(delta,new TextObject(label));
            number=updated;
        }
    }

    public static class EnhancementPatches
    {
        public const string Owner="DKX.BanditPopulationTuning.Enhancements.v1";
        public static readonly List<MethodBase> Targets=new List<MethodBase>();
        public static bool Ready {get;private set;}
        public static void Install()
        {
            var h=new Harmony(Owner);
            try
            {
                Hook(h,typeof(DefaultPartySizeLimitModel),"GetPartyMemberSizeLimit",nameof(PartySize));
                Hook(h,typeof(DefaultClanTierModel),"GetPartyLimitForTier",nameof(ClanParties));
                Hook(h,typeof(DefaultCharacterStatsModel),"MaxHitpoints",nameof(Health));
                Hook(h,typeof(DefaultSettlementLoyaltyModel),"CalculateLoyaltyChange",nameof(Loyalty));
                Hook(h,typeof(DefaultSettlementFoodModel),"CalculateTownFoodStocksChange",nameof(Food));
                Hook(h,typeof(DefaultSettlementMilitiaModel),"CalculateMilitiaChange",nameof(Militia));
                Hook(h,typeof(DefaultSettlementProsperityModel),"CalculateProsperityChange",nameof(Prosperity));
                Hook(h,typeof(DefaultSettlementSecurityModel),"CalculateSecurityChange",nameof(Security));
                Hook(h,typeof(DefaultSettlementTaxModel),"CalculateTownTax",nameof(Tax));
                var damage=AccessTools.TypeByName("SandBox.GameComponents.SandboxAgentApplyDamageModel") ?? throw new TypeLoadException("SandboxAgentApplyDamageModel");
                Hook(h,damage,"ApplyGeneralDamageModifiers",nameof(Damage));
                Ready=true;
            }
            catch {h.UnpatchAll(Owner);Targets.Clear();Ready=false;throw;}
        }
        private static void Hook(Harmony h,Type type,string name,string handler)
        {
            var method=AccessTools.DeclaredMethod(type,name) ?? throw new MissingMethodException(type.FullName,name);
            h.Patch(method,postfix:new HarmonyMethod(typeof(EnhancementPatches),handler){priority=Priority.Last});
            Targets.Add(method);
        }
        private static void PartySize(PartyBase __0,ref ExplainedNumber __result)
        {
            var s=Settings.Current;
            if((s.AIPartySizeMultiplier==1f && s.AIPartySizeBonus==0) || !EnhancementRules.AIParty(__0?.MobileParty)) return;
            float final=EnhancementRules.PartyCapacity(__result.ResultNumber,s.AIPartySizeMultiplier,s.AIPartySizeBonus);
            EnhancementRules.AddFinal(ref __result,final-__result.ResultNumber,"AI领主带兵上限：原结果×倍率＋额外人数");
        }
        private static void ClanParties(Clan __0,ref int __result)
        {
            if(Settings.Current.AIClanPartyBonus!=0 && EnhancementRules.AIClan(__0))
                __result=EnhancementRules.ClanCapacity(__result,Settings.Current.AIClanPartyBonus);
        }
        private static void Health(CharacterObject __0,ref ExplainedNumber __result)
        {
            if (__0?.IsHero!=true) return;
            int bonus=__0.HeroObject==Hero.MainHero ? Settings.Current.PlayerHealthBonus : Settings.Current.OtherHeroHealthBonus;
            EnhancementRules.AddFinal(ref __result,EnhancementRules.SafeInt(bonus,5000),"土匪与AI强化：英雄额外生命");
        }
        private static void Damage(in AttackInformation __0,ref float __result)
        {
            var s=Settings.Current;
            if(s.PlayerDamagePercent==0 && s.OtherHeroDamagePercent==0) return;
            var attacker=__0.AttackerAgentCharacter;
            __result=EnhancementRules.HeroDamage(__result,attacker?.IsHero==true,attacker!=null && attacker==Hero.MainHero?.CharacterObject,s);
        }
        private static void TownBonus(Town town,ref ExplainedNumber result,float bonus,string label)
        {
            if(bonus!=0 && EnhancementRules.Settlement(town?.Settlement))
                EnhancementRules.AddFinal(ref result,Rules.Safe(bonus,0f,10000f,0f),label);
        }
        private static void Loyalty(Town __0,ref ExplainedNumber __result) => TownBonus(__0,ref __result,Settings.Current.SettlementLoyaltyBonus,"AI定居点：每日忠诚额外增量");
        private static void Food(Town __0,ref ExplainedNumber __result) => TownBonus(__0,ref __result,Settings.Current.SettlementFoodBonus,"AI定居点：每日食物额外增量");
        private static void Prosperity(Town __0,ref ExplainedNumber __result) => TownBonus(__0,ref __result,Settings.Current.SettlementProsperityBonus,"AI定居点：每日繁荣额外增量");
        private static void Security(Town __0,ref ExplainedNumber __result) => TownBonus(__0,ref __result,Settings.Current.SettlementSecurityBonus,"AI定居点：每日治安额外增量");
        private static void Tax(Town __0,ref ExplainedNumber __result) => TownBonus(__0,ref __result,EnhancementRules.SafeInt(Settings.Current.SettlementTaxBonus,10000),"AI定居点：每日税收额外第纳尔");
        private static void Militia(Settlement __0,ref ExplainedNumber __result)
        {
            if(Settings.Current.SettlementMilitiaBonus!=0 && EnhancementRules.Settlement(__0))
                EnhancementRules.AddFinal(ref __result,Rules.Safe(Settings.Current.SettlementMilitiaBonus,0f,100f,0f),"AI定居点：每日民兵额外增量");
        }
        public static void Uninstall(){new Harmony(Owner).UnpatchAll(Owner);Targets.Clear();Ready=false;}
    }
}
