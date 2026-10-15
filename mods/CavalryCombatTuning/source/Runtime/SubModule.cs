using System;
using System.IO;
using TaleWorlds.Library;
using TaleWorlds.MountAndBlade;

namespace CavalryCombatTuning
{
    public sealed class SubModule : MBSubModuleBase
    {
        private static readonly string ModuleRoot = Path.GetFullPath(Path.Combine(
            Path.GetDirectoryName(typeof(SubModule).Assembly.Location), "..", ".."));
        private string _warning;
        private bool _installed;

        protected override void OnSubModuleLoad()
        {
            base.OnSubModuleLoad();
            try
            {
                RuntimePatches.CurrentSettings = Settings.Load(Path.Combine(ModuleRoot, "ModuleData", "settings.xml"));
            }
            catch (Exception error)
            {
                RuntimePatches.CurrentSettings = new Settings();
                _warning = "Cavalry Combat Tuning: 配置无效，已使用默认值；请查看 ModuleData/runtime.log。";
                Log("Invalid settings; defaults active. " + error);
            }
            try
            {
                RuntimePatches.Install();
                _installed = true;
                Settings s = RuntimePatches.CurrentSettings;
                Log("Loaded: charge=" + s.ChargeDamageMultiplier + "; movementPenalty="
                    + s.MountedMovementPenaltyMultiplier + "; AIOnly=" + s.MountedAccuracyAIOnly);
            }
            catch (Exception error)
            {
                _warning = "Cavalry Combat Tuning: 补丁加载失败，效果未启用；请查看 ModuleData/runtime.log。";
                Log("Patch installation failed. " + error);
            }
        }

        protected override void OnBeforeInitialModuleScreenSetAsRoot()
        {
            base.OnBeforeInitialModuleScreenSetAsRoot();
            if (_warning == null) return;
            InformationManager.DisplayMessage(new InformationMessage(_warning));
            _warning = null;
        }

        protected override void OnSubModuleUnloaded()
        {
            if (_installed) RuntimePatches.Uninstall();
            base.OnSubModuleUnloaded();
        }

        private static void Log(string message)
        {
            try
            {
                File.AppendAllText(Path.Combine(ModuleRoot, "ModuleData", "runtime.log"),
                    DateTime.Now.ToString("s") + " " + message + Environment.NewLine);
            }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }
    }
}
