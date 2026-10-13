using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using RaceTroopBuilder.Core;

namespace RaceTroopBuilder.Gui;

public partial class MainWindow : Window
{
    private Catalog? _catalog;
    private BuilderProject _project = new();
    private string? _projectFile;
    private string? _lastReport;
    private TroopInfo? _selected;
    private List<Loadout> _editedLoadouts = [];
    private bool _loading;
    private bool _busy;
    private bool _configurationNotApplied;
    private readonly Dictionary<string, TextBox> _skillInputs = new(StringComparer.Ordinal);
    private readonly Dictionary<string, TextBlock> _skillLabels = new(StringComparer.Ordinal);
    private readonly Dictionary<string, CheckBox> _skillResets = new(StringComparer.Ordinal);
    private readonly Dictionary<string, ComboBox> _slotChoices = new(StringComparer.Ordinal);

    public MainWindow()
    {
        InitializeComponent();
        ModPaths.Text = Discovery.DefaultModRoot();
        try { GamePath.Text = Discovery.FindGame(); } catch (DirectoryNotFoundException) { }
        SyncMetadata();
        foreach (var slot in Builder.Slots)
        {
            var panel = new StackPanel();
            panel.Children.Add(new TextBlock { Text = SlotLabel(slot), Foreground = new SolidColorBrush(Color.FromRgb(89, 112, 125)), FontSize = 12, Margin = new Thickness(0, 6, 0, 2) });
            var choice = new ComboBox { DisplayMemberPath = "Label", IsTextSearchEnabled = true, MaxDropDownHeight = 280 };
            _slotChoices[slot] = choice;
            choice.SelectionChanged += (_, _) =>
            {
                if (_loading || LoadoutChoice.SelectedIndex < 0 || LoadoutChoice.SelectedIndex >= _editedLoadouts.Count) return;
                var loadout = _editedLoadouts[LoadoutChoice.SelectedIndex];
                if (choice.SelectedItem is ItemInfo item && item.Id.Length > 0) loadout.Slots[slot] = item.Id;
                else loadout.Slots.Remove(slot);
            };
            panel.Children.Add(choice); SlotPanel.Children.Add(panel);
        }
        foreach (var id in Builder.SkillIds)
        {
            var panel = new StackPanel { Margin = new Thickness(0, 0, 6, 6) };
            var label = new TextBlock { Text = SkillLabel(id), FontSize = 12 };
            var input = new TextBox();
            var reset = new CheckBox { Content = "恢复原版", FontSize = 11 };
            reset.Checked += (_, _) => { input.Text = ""; input.IsEnabled = false; };
            reset.Unchecked += (_, _) => input.IsEnabled = true;
            _skillInputs[id] = input; _skillLabels[id] = label; _skillResets[id] = reset;
            panel.Children.Add(label); panel.Children.Add(input); panel.Children.Add(reset); SkillPanel.Children.Add(panel);
        }
        UpdateProjectText();
    }
    private static string SkillLabel(string id) => id switch
    {
        "OneHanded" => "单手", "TwoHanded" => "双手", "Polearm" => "长杆", "Bow" => "弓",
        "Crossbow" => "弩", "Throwing" => "投掷", "Athletics" => "跑动", "Riding" => "骑术", _ => id
    };
    private Dictionary<string, int>? CaptureSkills()
    {
        var values = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (var (id, input) in _skillInputs)
        {
            var text = input.Text.Trim();
            if (text.Length == 0) continue;
            if (!int.TryParse(text, out var value) || value < 0) throw new InvalidDataException(SkillLabel(id) + "须为非负整数。");
            values[id] = value;
        }
        return values.Count == 0 ? null : values;
    }

    private string NameLanguage => _project.DisplayLanguage;
    private void LanguageChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading || LanguageChoice == null || TroopTree == null) return;
        var selected = _selected;
        _project.DisplayLanguage = LanguageChoice.SelectedIndex == 1 ? "en" : "zh-CN";
        if (_catalog != null) foreach (var item in _catalog.Items.Values) item.Language = NameLanguage;
        RenderTree();
        // Preserve unapplied equipment and armor drafts when changing display language.
        _selected = selected;
        if (selected != null) SelectedName.Text = selected.DisplayName(NameLanguage);
        FillSlots(); UpdateProjectText();
    }
    private void RaceChanged(object sender, SelectionChangedEventArgs e)
    {
        if (RaceArmorText == null) return;
        var race = RaceChoice.SelectedItem as RaceInfo;
        var a = race?.DefaultArmor;
        RaceArmorText.Text = a == null ? "未声明协议默认值；沿用时不干预现有机制。" : $"种族默认：头 {a.Head} / 身 {a.Body} / 臂 {a.Arms} / 腿 {a.Legs}";
    }
    private void ArmorModeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ArmorInputs == null) return;
        ArmorInputs.IsEnabled = ArmorMode.SelectedIndex is 1 or 2;
        if (_loading || ArmorMode.SelectedIndex != 2) return;
        try
        {
            RequireCatalog();
            if (_selected == null) throw new InvalidOperationException("请先选择一个兵种。");
            FillArmor(Builder.OriginalArmor(_catalog!, _selected));
        }
        catch (Exception error) { ArmorMode.SelectedIndex = 0; ShowError(error); }
    }
    private void FillArmor(ArmorSettings? armor)
    {
        ArmorHead.Text = (armor?.Head ?? 0).ToString(); ArmorBody.Text = (armor?.Body ?? 0).ToString();
        ArmorArms.Text = (armor?.Arms ?? 0).ToString(); ArmorLegs.Text = (armor?.Legs ?? 0).ToString();
    }
    private ArmorSettings? CaptureArmor()
    {
        if (ArmorMode.SelectedIndex is not (1 or 2)) return null;
        int Value(TextBox text)
        {
            if (!int.TryParse(text.Text, out var value) || value < 0 || value > 500) throw new InvalidDataException("护甲必须为 0～500 的整数。");
            return value;
        }
        return new() { Mode = "override", Head = Value(ArmorHead), Body = Value(ArmorBody), Arms = Value(ArmorArms), Legs = Value(ArmorLegs) };
    }
    private static string SlotLabel(string slot) => slot switch
    {
        "Item0" => "Item0 · 武器槽 1", "Item1" => "Item1 · 武器槽 2", "Item2" => "Item2 · 武器槽 3", "Item3" => "Item3 · 武器槽 4",
        "Head" => "Head · 头部", "Cape" => "Cape · 披肩", "Body" => "Body · 身甲", "Leg" => "Leg · 腿部", "Gloves" => "Gloves · 手套",
        "Horse" => "Horse · 坐骑", _ => "HorseHarness · 马具"
    };
    private void SyncMetadata()
    { _loading = true; ModuleIdText.Text = _project.ModuleId; ModuleNameText.Text = _project.ModuleName; VersionText.Text = _project.Version; LanguageChoice.SelectedIndex = NameLanguage == "en" ? 1 : 0; _loading = false; }
    private void CaptureMetadata()
    {
        _project.ModuleId = ModuleIdText.Text.Trim(); _project.ModuleName = ModuleNameText.Text.Trim(); _project.Version = VersionText.Text.Trim();
        _project.GameRoot = GamePath.Text.Trim(); _project.ModRoots = Roots();
    }
    private List<string> Roots() => ModPaths.Text.Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries).Select(x => x.Trim()).Where(x => x.Length > 0).ToList();
    private void UpdateProjectText()
    {
        if (ProjectText == null) return;
        ProjectText.Text = Json.Write(_project);
        var count = _catalog == null ? _project.Rules.Sum(x => x.TroopIds.Count) : _project.Rules.SelectMany(x => Builder.Select(_catalog, x)).Distinct().Count();
        StatusText.Text = $"{(_catalog == null ? "未扫描" : _catalog.GameVersion)} · {count} 个已配置兵种 · {(_projectFile == null ? "未保存工程" : Path.GetFileName(_projectFile))}";
    }
    private void ShowError(Exception error) { OutputText.Text = error.Message; StatusText.Text = "操作未完成 · " + error.Message; }
    private async Task Run(Func<Task> action)
    {
        if (_busy) return;
        _busy = true; Editor.IsEnabled = false; ScanButton.IsEnabled = false;
        try { await action(); } catch (Exception error) { ShowError(error); }
        finally { _busy = false; Editor.IsEnabled = true; ScanButton.IsEnabled = true; }
    }
    private Task Run(Action action) => Run(() => { action(); return Task.CompletedTask; });

    private async Task ScanCatalog()
    {
        StatusText.Text = "正在扫描原版兵种、物品和种族入口…";
        var game = GamePath.Text.Trim(); var roots = Roots();
        _catalog = await Task.Run(() => Discovery.Scan(game.Length > 0 ? game : null, roots));
        GamePath.Text = _catalog.GameRoot; ModPaths.Text = string.Join(Environment.NewLine, _catalog.ModRoots);
        var previousRace = (RaceChoice.SelectedItem as RaceInfo)?.Id;
        RaceChoice.ItemsSource = _catalog.Races.OrderBy(x => x.ModuleId).ToList();
        RaceChoice.SelectedItem = _catalog.Races.FirstOrDefault(x => x.Id == previousRace);
        foreach (var item in _catalog.Items.Values) item.Language = NameLanguage;
        RenderTree();
        OutputText.Text = $"扫描完成：{_catalog.Troops.Count} 个士兵 / 雇佣兵，{_catalog.Items.Count} 个原版物品，{_catalog.Races.Count} 个自定义种族。\n\n依赖种族 Mod 在上，生成的兵种替换 Mod 在下。\n请选择兵种和种族，再应用配置。\n\n" +
            string.Join("\n", _catalog.Issues.Select(x => x.Message));
        CaptureMetadata(); UpdateProjectText();
    }
    private async void ScanClick(object sender, RoutedEventArgs e) => await Run(ScanCatalog);
    private void GameBrowseClick(object sender, RoutedEventArgs e)
    { var dialog = new OpenFolderDialog { Title = "选择 Bannerlord 游戏根目录" }; if (dialog.ShowDialog(this) == true) GamePath.Text = dialog.FolderName; }
    private void ModsBrowseClick(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFolderDialog { Title = "选择种族 Mod 工程、模块目录或 Modules 根目录" };
        if (dialog.ShowDialog(this) == true) ModPaths.Text = string.Join(Environment.NewLine, Roots().Append(dialog.FolderName).Distinct(StringComparer.OrdinalIgnoreCase));
    }

    private void RenderTree()
    {
        if (_catalog == null) return;
        TroopTree.Items.Clear(); _selected = null;
        var filter = TroopSearch.Text.Trim();
        foreach (var culture in _catalog.Troops.Values.GroupBy(x => x.Culture).OrderBy(x => x.Key))
        {
            var matching = culture.Where(x => filter.Length == 0 || x.SearchText.Contains(filter, StringComparison.OrdinalIgnoreCase)).ToList();
            if (matching.Count == 0) continue;
            var header = new TreeViewItem { Header = $"{CultureLabel(culture.Key)} · {culture.Count()} 兵种", IsExpanded = filter.Length > 0 };
            if (filter.Length > 0)
                foreach (var troop in matching.OrderBy(x => x.Level).ThenBy(x => x.Id)) header.Items.Add(TreeNode(troop, [], false));
            else
            {
                var incoming = culture.SelectMany(x => x.Upgrades).ToHashSet(StringComparer.Ordinal);
                var covered = new HashSet<string>(StringComparer.Ordinal);
                foreach (var troop in culture.Where(x => x.IsBasicTroop || !incoming.Contains(x.Id)).OrderBy(x => x.Level).ThenBy(x => x.Id))
                { header.Items.Add(TreeNode(troop, [], true)); foreach (var id in Builder.Select(_catalog, new TroopRule { RootIds = [troop.Id] })) covered.Add(id); }
                foreach (var troop in culture.Where(x => !covered.Contains(x.Id)).OrderBy(x => x.Id)) header.Items.Add(TreeNode(troop, [], true));
            }
            TroopTree.Items.Add(header);
        }
    }
    private TreeViewItem TreeNode(TroopInfo troop, HashSet<string> ancestors, bool descendants)
    {
        var configured = _project.Rules.Any(rule => Builder.Select(_catalog!, rule).Contains(troop.Id));
        var node = new TreeViewItem { Header = (configured ? "● " : "") + $"{troop.DisplayName(NameLanguage)} [{troop.Id}] · Lv{troop.Level}", Tag = troop, ToolTip = troop.Id };
        if (descendants && ancestors.Add(troop.Id))
            foreach (var id in troop.Upgrades)
                if (!ancestors.Contains(id) && _catalog!.Troops.TryGetValue(id, out var child)) node.Items.Add(TreeNode(child, new(ancestors), true));
        return node;
    }
    private static string CultureLabel(string culture) => culture switch
    { "empire" => "帝国", "aserai" => "阿塞莱", "battania" => "巴旦尼亚", "khuzait" => "库赛特", "sturgia" => "斯特吉亚", "vlandia" => "瓦兰迪亚", "neutral_culture" => "中立 / 雇佣兵", _ => culture };
    private void TroopSearchChanged(object sender, TextChangedEventArgs e) { if (TroopTree != null && !_busy) RenderTree(); }
    private void TroopSelected(object sender, RoutedPropertyChangedEventArgs<object> e)
    {
        if (e.NewValue is not TreeViewItem { Tag: TroopInfo troop }) return;
        try { SelectTroop(troop); } catch (Exception error) { ShowError(error); }
    }
    private void SelectTroop(TroopInfo troop)
    {
        _selected = troop;
        SelectedName.Text = troop.DisplayName(NameLanguage); SelectedMeta.Text = $"{troop.Id} · Lv{troop.Level}";
        SelectedMeta.ToolTip = $"{CultureLabel(troop.Culture)} · {troop.Upgrades.Count} 个升级目标";
        var rule = _project.Rules.FirstOrDefault(x => Builder.Select(_catalog!, x).Contains(troop.Id));
        if (rule != null)
        {
            RaceChoice.SelectedItem = _catalog!.Races.FirstOrDefault(x => x.ModuleId == rule.RaceModule && x.Id == rule.RaceId);
            GenderChoice.SelectedIndex = rule.IsFemale == null ? 0 : rule.IsFemale.Value ? 1 : 2;
            FaceChoice.SelectedIndex = rule.FaceMode == "fixed" ? 1 : 0;
            AgeText.Text = rule.Age?.ToString() ?? ""; StripArmor.IsChecked = rule.StripArmor;
        }
        foreach (var id in Builder.SkillIds)
        {
            var native = troop.Element.Element("skills")?.Elements("skill").LastOrDefault(x => (string?)x.Attribute("id") == id);
            _skillLabels[id].Text = SkillLabel(id) + " · 原版 " + ((string?)native?.Attribute("value") ?? "未显式配置");
            _skillResets[id].IsChecked = false;
            _skillInputs[id].Text = rule?.Skills?.TryGetValue(id, out var value) == true ? value.ToString() : "";
        }
        var useOriginalArmor = rule?.Armor?.Mode != "override" && ArmorMode.SelectedIndex == 2;
        var armor = useOriginalArmor ? Builder.OriginalArmor(_catalog!, troop) : rule?.Armor;
        _loading = true;
        ArmorMode.SelectedIndex = rule?.Armor?.Mode == "override" ? 1 : useOriginalArmor ? 2 : 0;
        FillArmor(armor);
        _loading = false;
        ReplaceEquipment.IsChecked = rule?.BattleLoadouts != null;
        var originals = Builder.Loadouts(_catalog!, troop.Element).Where(x => x.Type == "Battle").Select(x => x.Loadout).ToList();
        _editedLoadouts = (rule?.BattleLoadouts ?? originals).Select(Clone).ToList();
        if (_editedLoadouts.Count == 0) _editedLoadouts.Add(new());
        RefreshLoadouts(0);
    }
    private static Loadout Clone(Loadout original) => new() { Slots = new(original.Slots, StringComparer.Ordinal) };
    private void RefreshLoadouts(int index)
    {
        _loading = true;
        LoadoutChoice.ItemsSource = Enumerable.Range(1, _editedLoadouts.Count).Select(x => "战斗装备套 " + x).ToList();
        LoadoutChoice.SelectedIndex = Math.Clamp(index, 0, _editedLoadouts.Count - 1);
        _loading = false; FillSlots();
    }
    private void FillSlots()
    {
        if (_catalog == null || LoadoutChoice.SelectedIndex < 0 || LoadoutChoice.SelectedIndex >= _editedLoadouts.Count) return;
        _loading = true;
        var current = _editedLoadouts[LoadoutChoice.SelectedIndex]; var filter = ItemSearch.Text.Trim();
        foreach (var (slot, choice) in _slotChoices)
        {
            var candidates = _catalog.Items.Values.Where(item => slot switch
            {
                "Head" => item.Type == "HeadArmor", "Cape" => item.Type == "Cape", "Body" => item.Type == "BodyArmor", "Leg" => item.Type == "LegArmor", "Gloves" => item.Type == "HandArmor",
                "Horse" => item.Type == "Horse", "HorseHarness" => item.Type == "HorseHarness", _ => Builder.IsWeapon(item.Type)
            }).Where(x => x.SearchText.Contains(filter, StringComparison.OrdinalIgnoreCase)).OrderBy(x => x.Id).ToList();
            var cleared = StripArmor.IsChecked == true && Builder.ArmorSlots.Contains(slot);
            choice.IsEnabled = !cleared;
            var selectedId = cleared ? null : current.Slots.GetValueOrDefault(slot);
            if (selectedId != null && _catalog.Items.TryGetValue(selectedId, out var selected) && !candidates.Any(x => x.Id == selectedId)) candidates.Insert(0, selected);
            candidates.Insert(0, new("", "（空槽）", "", ""));
            choice.ItemsSource = candidates;
            choice.SelectedItem = candidates.FirstOrDefault(x => x.Id == selectedId) ?? candidates[0];
        }
        _loading = false;
    }
    private void LoadoutChanged(object sender, SelectionChangedEventArgs e) { if (!_loading) FillSlots(); }
    private void ArmorChanged(object sender, RoutedEventArgs e) { if (!_loading) FillSlots(); }
    private void ItemSearchChanged(object sender, TextChangedEventArgs e) { if (!_loading && SlotPanel != null) FillSlots(); }
    private void AddLoadoutClick(object sender, RoutedEventArgs e)
    {
        if (_editedLoadouts.Count == 0) return;
        _editedLoadouts.Add(Clone(_editedLoadouts[Math.Max(0, LoadoutChoice.SelectedIndex)])); RefreshLoadouts(_editedLoadouts.Count - 1);
    }
    private void DeleteLoadoutClick(object sender, RoutedEventArgs e)
    {
        if (_editedLoadouts.Count <= 1) { StatusText.Text = "至少保留一套战斗装备。"; return; }
        var index = LoadoutChoice.SelectedIndex; if (index < 0) return;
        _editedLoadouts.RemoveAt(index); RefreshLoadouts(Math.Min(index, _editedLoadouts.Count - 1));
    }
    private List<string> ScopeIds()
    {
        if (_catalog == null || _selected == null) throw new InvalidOperationException("请先扫描并选择一个兵种。");
        return Builder.Select(_catalog, ScopeChoice.SelectedIndex switch
        { 1 => new TroopRule { RootIds = [_selected.Id] }, 2 => new TroopRule { Culture = _selected.Culture }, _ => new TroopRule { TroopIds = [_selected.Id] } });
    }
    private void RemoveTargets(List<string> targets)
    {
        var set = targets.ToHashSet(StringComparer.Ordinal);
        foreach (var rule in _project.Rules)
        {
            rule.TroopIds = Builder.Select(_catalog!, rule).Where(x => !set.Contains(x)).ToList();
            rule.RootIds.Clear(); rule.Culture = null;
        }
        _project.Rules.RemoveAll(x => x.TroopIds.Count == 0);
    }
    private void RequireAppliedConfiguration()
    {
        if (_configurationNotApplied)
            throw new InvalidOperationException("上次应用配置未成功，当前工程仍是旧配置。请修正错误并重新点击“应用配置到所选范围”；已阻止保存、导出和安装旧配置。");
    }
    private void ApplyConfiguration()
    {
        _configurationNotApplied = true;
        _lastReport = null;
        RequireCatalog();
        var targets = ScopeIds();
        if (RaceChoice.SelectedItem is not RaceInfo race) throw new InvalidOperationException("请选择依赖种族。");
        int? age = null;
        if (AgeText.Text.Trim().Length > 0)
        { if (!int.TryParse(AgeText.Text.Trim(), out var number)) throw new InvalidDataException("年龄应为整数。"); age = number; }
        var rule = new TroopRule { TroopIds = targets, RaceModule = race.ModuleId, RaceId = race.Id,
            IsFemale = GenderChoice.SelectedIndex switch { 1 => true, 2 => false, _ => null }, Age = age,
            FaceMode = FaceChoice.SelectedIndex == 1 ? "fixed" : "preserve", StripArmor = StripArmor.IsChecked == true, Armor = CaptureArmor(), Skills = CaptureSkills(),
            BattleLoadouts = ReplaceEquipment.IsChecked == true ? _editedLoadouts.Select(Clone).ToList() : null };
        CaptureMetadata();
        // Keep the prior project until the candidate passes validation.
        var candidate = System.Text.Json.JsonSerializer.Deserialize<BuilderProject>(Json.Write(_project), Json.Options)!;
        var previous = _project; _project = candidate;
        var preserved = targets.GroupBy(id =>
        {
            var original = previous.Rules.FirstOrDefault(x => Builder.Select(_catalog!, x).Contains(id));
            return Json.Write(new { original?.Name, original?.CivilianLoadouts, original?.Skills });
        }).ToList();
        RemoveTargets(targets);
        foreach (var group in preserved)
        {
            var newRule = System.Text.Json.JsonSerializer.Deserialize<TroopRule>(Json.Write(rule), Json.Options)!;
            var original = previous.Rules.FirstOrDefault(x => Builder.Select(_catalog!, x).Contains(group.First()));
            newRule.TroopIds = group.ToList(); newRule.Name = original?.Name;
            newRule.CivilianLoadouts = original?.CivilianLoadouts?.Select(Clone).ToList();
            var skills = original?.Skills == null ? new Dictionary<string, int>() : new Dictionary<string, int>(original.Skills);
            foreach (var id in Builder.SkillIds)
                if (_skillResets[id].IsChecked == true) skills.Remove(id);
            foreach (var (id, value) in rule.Skills ?? []) skills[id] = value;
            newRule.Skills = skills.Count == 0 ? null : skills;
            _project.Rules.Add(newRule);
        }
        var report = Builder.Validate(_catalog!, _project);
        if (report.Status != "pass")
        {
            _project = previous;
            throw new InvalidDataException("应用配置失败：候选 " + report.Targets.Count + " 个兵种未保存；当前工程仍有 " +
                _project.Rules.SelectMany(x => Builder.Select(_catalog!, x)).Distinct().Count() + " 个已配置兵种。\n" +
                string.Join("\n", report.Issues.Where(x => x.Severity == "error").Select(x => x.Subject + ": " + x.Message)));
        }
        _configurationNotApplied = false;
        _lastReport = null; UpdateProjectText(); ShowReport(report);
        var selectedId = _selected!.Id; RenderTree(); SelectTroop(_catalog!.Troops[selectedId]);
    }
    private async void ApplyClick(object sender, RoutedEventArgs e) => await Run(ApplyConfiguration);
    private async void RemoveRuleClick(object sender, RoutedEventArgs e) => await Run(() =>
    { var ids = ScopeIds(); RemoveTargets(ids); _configurationNotApplied = false; _lastReport = null; UpdateProjectText(); RenderTree(); OutputText.Text = $"已撤销 {ids.Count} 个兵种的替换配置。"; });
    private void ShowReport(CheckReport report)
    {
        OutputText.Text = $"{(report.Status == "pass" ? "检查通过" : "检查未通过")} · {report.Targets.Count} 个目标兵种 · {report.TransformChecks} 个节点转换核对\n\n加载顺序（从上到下）：\n" + string.Join(" → ", report.LoadOrder) +
            "\n\n" + string.Join("\n", report.Issues.Select(x => $"[{x.Severity}] {x.Subject}: {x.Message}")) + "\n\n" + report.RuntimeTesting;
        if (report.ModulePath != null) OutputText.Text += "\n\n导出目录：" + report.ModulePath;
    }
    private async void ValidateClick(object sender, RoutedEventArgs e) => await Run(() =>
    { RequireAppliedConfiguration(); RequireCatalog(); CaptureMetadata(); UpdateProjectText(); ShowReport(Builder.Validate(_catalog!, _project)); });
    private async void PreviewClick(object sender, RoutedEventArgs e) => await Run(() =>
    {
        RequireAppliedConfiguration(); RequireCatalog(); CaptureMetadata(); UpdateProjectText(); var report = Builder.Validate(_catalog!, _project); ShowReport(report);
        DiffText.Text = report.Status == "pass" ? Json.Write(Builder.Preview(_catalog!, _project)) : "先修复检查错误，再查看修改对比。";
    });
    private void RequireCatalog()
    {
        if (_catalog == null) throw new InvalidOperationException("请先扫描目录。");
        if (!string.Equals(Path.GetFullPath(GamePath.Text.Trim()), _catalog.GameRoot, StringComparison.OrdinalIgnoreCase)
            || !Roots().Select(Path.GetFullPath).SequenceEqual(_catalog.ModRoots, StringComparer.OrdinalIgnoreCase))
            throw new InvalidOperationException("目录已改变，请重新扫描后继续。");
    }
    private async void NewProjectClick(object sender, RoutedEventArgs e) => await Run(() =>
    { _project = new(); _projectFile = null; _lastReport = null; _configurationNotApplied = false; SyncMetadata(); UpdateProjectText(); if (_catalog != null) RenderTree(); });
    public async Task OpenProject(string path)
    {
        await Run(async () =>
        {
            var project = Builder.ReadProject(path);
            _project = project; _projectFile = Path.GetFullPath(path); _lastReport = null; _configurationNotApplied = false;
            GamePath.Text = project.GameRoot ?? GamePath.Text; ModPaths.Text = string.Join(Environment.NewLine, project.ModRoots.Count > 0 ? project.ModRoots : [Discovery.DefaultModRoot()]);
            SyncMetadata(); await ScanCatalog(); UpdateProjectText(); ShowReport(Builder.Validate(_catalog!, _project));
        });
    }
    private async void OpenClick(object sender, RoutedEventArgs e)
    { var dialog = new OpenFileDialog { Filter = "拼装工程 JSON|*.json", Title = "打开兵种拼装工程" }; if (dialog.ShowDialog(this) == true) await OpenProject(dialog.FileName); }
    private async void SaveClick(object sender, RoutedEventArgs e) => await Run(() =>
    {
        RequireAppliedConfiguration();
        var dialog = new SaveFileDialog { Filter = "拼装工程 JSON|*.json", FileName = _projectFile ?? "my-race-troops.json" };
        if (dialog.ShowDialog(this) != true) return;
        CaptureMetadata(); Json.Save(dialog.FileName, _project); _projectFile = dialog.FileName; UpdateProjectText();
    });
    private async void BuildClick(object sender, RoutedEventArgs e) => await Run(async () =>
    {
        RequireAppliedConfiguration(); RequireCatalog(); CaptureMetadata(); UpdateProjectText();
        var validation = Builder.Validate(_catalog!, _project); if (validation.Status != "pass") { ShowReport(validation); return; }
        var dialog = new OpenFolderDialog { Title = "选择导出根目录（将创建带时间戳的独立构建目录）" };
        if (dialog.ShowDialog(this) != true) return;
        var output = Path.Combine(dialog.FolderName, _project.ModuleId + "-" + DateTimeOffset.Now.ToString("yyyyMMdd-HHmmss-fff"));
        StatusText.Text = "正在生成并核对兵种转换…";
        var report = await Task.Run(() => Builder.Build(_catalog!, _project, output)); ShowReport(report);
        if (report.Status == "pass")
        {
            _lastReport = Path.Combine(output, _project.ModuleId + ".validation.json");
            var package = Builder.Package(_lastReport, Path.Combine(output, _project.ModuleId + "-" + _project.Version + ".zip"));
            OutputText.Text += "\n交付包：" + package; StatusText.Text = "Mod 与 ZIP 已导出 · 可使用“安装最近构建”安装";
        }
    });
    private async void InstallClick(object sender, RoutedEventArgs e) => await Run(async () =>
    {
        RequireAppliedConfiguration();
        if (_lastReport == null) throw new InvalidOperationException("请先导出当前工程。修改配置后应重新导出。");
        RequireCatalog(); StatusText.Text = "正在检查依赖并安装当前模块…";
        var installGame = GamePath.Text.Trim();
        var result = await Task.Run(() => Builder.Install(_lastReport, installGame));
        OutputText.Text = Json.Write(result); StatusText.Text = "安装完成 · 旧版已备份 · 请在启动器中按加载顺序启用";
    });

    public async Task SmokeTest(string pngPath)
    {
        await ScanCatalog();
        if (_catalog!.Troops.Count == 0 || _catalog.Races.Count == 0) throw new InvalidDataException("扫描未返回目录。");
        _project.ModuleId = "RaceTroopBuilderDemo"; _project.ModuleName = "Race Troop Builder Demo"; SyncMetadata();
        SelectTroop(_catalog.Troops["imperial_recruit"]);
        RaceChoice.SelectedItem = _catalog.Races.Single(x => x.ModuleId == "YueQingShuRace" && x.Id == "yqs_default");
        GenderChoice.SelectedIndex = 1; FaceChoice.SelectedIndex = 1; AgeText.Text = "25";
        StripArmor.IsChecked = true; ScopeChoice.SelectedIndex = 1;
        ApplyConfiguration();
        if (_project.Rules.Count == 0) throw new InvalidDataException(OutputText.Text);
        var report = Builder.Validate(_catalog, _project);
        if (report.Status != "pass" || report.Targets.Count < 10) throw new InvalidDataException(Json.Write(report));
        _skillInputs["Athletics"].Text = "150"; _skillInputs["Riding"].Text = "0";
        LanguageChoice.SelectedIndex = 1; LanguageChoice.SelectedIndex = 0;
        if (_skillInputs["Athletics"].Text != "150") throw new InvalidDataException("语言切换丢失技能草稿。");
        ApplyConfiguration();
        foreach (var target in Builder.Select(_catalog, new() { RootIds = ["imperial_recruit"] }))
            if (_project.Rules.Single(x => x.TroopIds.Contains(target)).Skills?["Athletics"] != 150)
                throw new InvalidDataException("GUI 批量技能覆盖失败。");
        SelectTroop(_catalog.Troops["imperial_recruit"]);
        if (_skillInputs["Riding"].Text != "0") throw new InvalidDataException("GUI 零值回读失败。");
        _skillResets["Athletics"].IsChecked = true; ScopeChoice.SelectedIndex = 0; ApplyConfiguration();
        if (_project.Rules.Single(x => x.TroopIds.Contains("imperial_recruit")).Skills!.ContainsKey("Athletics"))
            throw new InvalidDataException("GUI 恢复原版未删除覆盖。");
        var veteranRule = _project.Rules.First(x => !x.TroopIds.Contains("imperial_recruit"));
        veteranRule.Skills!["Bow"] = 77;
        _skillInputs["Athletics"].Text = "160"; _skillInputs["Riding"].Text = "";
        ScopeChoice.SelectedIndex = 1; ApplyConfiguration();
        if (_project.Rules.First(x => x.TroopIds.Contains(veteranRule.TroopIds[0])).Skills!["Bow"] != 77)
            throw new InvalidDataException("GUI 批量修改丢失其他节点技能。");
        var mercenary = _catalog.Troops["western_mercenary"];
        SelectTroop(mercenary);
        if (SelectedName.Text != mercenary.NameZh || mercenary.NameZh.Length == 0)
            throw new InvalidDataException("GUI 雇佣兵官方中文未显示。");
        TroopSearch.Text = mercenary.NameZh;
        if (TroopTree.Items.Count == 0) throw new InvalidDataException("雇佣兵中文搜索失败。");
        TroopSearch.Text = "";
        SelectTroop(_catalog.Troops["imperial_recruit"]);
        var sample = _catalog.Items.Values.First(x => x.Type == "OneHandedWeapon");
        _slotChoices["Item0"].SelectedItem = _slotChoices["Item0"].Items.Cast<ItemInfo>().First(x => x.Id == sample.Id);
        AddLoadoutClick(this, new()); ReplaceEquipment.IsChecked = true; ScopeChoice.SelectedIndex = 0; ApplyConfiguration();
        var editedRule = _project.Rules.Single(x => x.TroopIds.Contains("imperial_recruit"));
        if (editedRule.BattleLoadouts?.Count != 5 || editedRule.BattleLoadouts[0].Slots["Item0"] != sample.Id)
            throw new InvalidDataException("GUI 装备选择、复制套或规则更新未生效。");
        editedRule.Name = "Imperial Recruit";
        editedRule.CivilianLoadouts = [new() { Slots = new() { ["Item0"] = sample.Id } }];
        ApplyConfiguration();
        var retained = _project.Rules.Single(x => x.TroopIds.Contains("imperial_recruit"));
        if (retained.Name != "Imperial Recruit" || retained.CivilianLoadouts?.Single().Slots["Item0"] != sample.Id)
            throw new InvalidDataException("GUI 丢失了 AI 配置的显示名或平民装备。");
        retained.Name = null; retained.CivilianLoadouts = null;
        LanguageChoice.SelectedIndex = 1;
        if (SelectedName.Text != _catalog.Troops["imperial_recruit"].NameEn) throw new InvalidDataException("英文切换未生效。");
        LanguageChoice.SelectedIndex = 0;
        if (SelectedName.Text != "帝国新兵") throw new InvalidDataException("中文切换未生效。");
        ArmorMode.SelectedIndex = 1; ArmorHead.Text = "15"; ArmorBody.Text = "30"; ArmorArms.Text = "20"; ArmorLegs.Text = "25";
        ScopeChoice.SelectedIndex = 0; ApplyConfiguration();
        if (_project.Rules.Single(x => x.TroopIds.Contains("imperial_recruit")).Armor?.Body != 30) throw new InvalidDataException("护甲覆盖未保存。");
        var nativeArmor = Builder.OriginalArmor(_catalog, _catalog.Troops["imperial_recruit"]);
        ArmorMode.SelectedIndex = 2;
        if (!ArmorInputs.IsEnabled || Json.Write(CaptureArmor()) != Json.Write(nativeArmor))
            throw new InvalidDataException("原兵种护甲未自动填入或不可编辑。");
        ArmorBody.Text = "0";
        LanguageChoice.SelectedIndex = 1; LanguageChoice.SelectedIndex = 0;
        if (ArmorMode.SelectedIndex != 2 || ArmorBody.Text != "0") throw new InvalidDataException("语言切换丢失原兵种护甲草稿。");
        ApplyConfiguration();
        var savedArmor = _project.Rules.Single(x => x.TroopIds.Contains("imperial_recruit")).Armor;
        if (savedArmor?.Mode != "override" || savedArmor.Body != 0 || savedArmor.Head != nativeArmor.Head
            || savedArmor.Arms != nativeArmor.Arms || savedArmor.Legs != nativeArmor.Legs || ArmorBody.Text != "0")
            throw new InvalidDataException("原兵种护甲手动修改未保存或回读被原值覆盖。");
        var roundtrip = System.Text.Json.JsonSerializer.Deserialize<BuilderProject>(Json.Write(_project), Json.Options)!;
        if (roundtrip.Rules.Single(x => x.TroopIds.Contains("imperial_recruit")).Armor?.Body != 0)
            throw new InvalidDataException("原兵种护甲工程回读失败。");
        ArmorMode.SelectedIndex = 2;
        if (ArmorBody.Text != nativeArmor.Body.ToString()) throw new InvalidDataException("重新选择未恢复原兵种基准。");
        SelectTroop(mercenary);
        if (Json.Write(CaptureArmor()) != Json.Write(Builder.OriginalArmor(_catalog, mercenary)))
            throw new InvalidDataException("切换兵种未刷新原版护甲。");
        SelectTroop(_catalog.Troops["imperial_recruit"]);
        if (ArmorBody.Text != "0") throw new InvalidDataException("切换兵种丢失已保存的护甲修改。");
        ArmorMode.SelectedIndex = 0;
        // Regression: the standalone Tianxiang provider also appears in the collection.
        var savedProject = _project;
        _project = new BuilderProject { ModuleId = "CataphractRegression", ModuleName = "Cataphract Regression", Rules =
        [
            new() { TroopIds = ["imperial_legionary"], RaceModule = "YueQingShuOutfit2Race", RaceId = "yqs2_outfit2", IsFemale = true, StripArmor = true },
            new() { TroopIds = ["imperial_elite_menavliaton"], RaceModule = "YueQingShuRace", RaceId = "yqs_default", IsFemale = true, StripArmor = true },
            new() { TroopIds = ["imperial_palatine_guard"], RaceModule = "BaiMoQingOutfit2Race", RaceId = "bmq2_outfit2", IsFemale = true, StripArmor = true },
            new() { TroopIds = ["imperial_sergeant_crossbowman"], RaceModule = "BaiMoQingRace", RaceId = "bmq_default", IsFemale = true, StripArmor = true }
        ] };
        SelectTroop(_catalog.Troops["imperial_elite_cataphract"]);
        RaceChoice.SelectedItem = _catalog.Races.Single(x => x.ModuleId == "TianxiangT5PVERace" && x.Id == "txt5pve");
        GenderChoice.SelectedIndex = 1; FaceChoice.SelectedIndex = 1; AgeText.Text = "";
        StripArmor.IsChecked = true; ArmorMode.SelectedIndex = 0; ScopeChoice.SelectedIndex = 0;
        foreach (var loadout in _editedLoadouts)
        {
            loadout.Slots["Item0"] = "empire_lance_3_t5";
            loadout.Slots["Item1"] = "empire_mace_5_t5";
            loadout.Slots.Remove("Item2"); loadout.Slots.Remove("Item3");
        }
        RefreshLoadouts(0); ReplaceEquipment.IsChecked = true; ApplyConfiguration();
        RequireAppliedConfiguration();
        var catReport = Builder.Build(_catalog, _project, Path.Combine(Path.GetDirectoryName(Path.GetFullPath(pngPath))!, "cataphract-regression"));
        if (catReport.Status != "pass" || catReport.Targets.Count != 5 || !catReport.Targets.Contains("imperial_elite_cataphract"))
            throw new InvalidDataException("Tianxiang T5 装备修改后未导出第五个兵种：" + Json.Write(catReport));
        var exported = System.Xml.Linq.XDocument.Load(Path.Combine(catReport.ModulePath!, "ModuleData", "rtb_troops.xslt"))
            .Descendants("NPCCharacter").Single(x => (string?)x.Attribute("id") == "imperial_elite_cataphract");
        foreach (var roster in exported.Descendants("EquipmentRoster").Where(x => (string?)x.Attribute("equipmentType") == "Battle"))
        {
            var slots = roster.Elements("equipment").ToDictionary(x => (string)x.Attribute("slot")!, x => (string)x.Attribute("id")!);
            if (slots["Item0"] != "Item.empire_lance_3_t5" || slots["Item1"] != "Item.empire_mace_5_t5" || slots.ContainsKey("Item2") || slots.ContainsKey("Item3"))
                throw new InvalidDataException("具装骑兵装备改动未进入最终 XSLT。");
        }
        // A rejected candidate cannot subsequently save or export the previous project as if it succeeded.
        AgeText.Text = "17";
        try { ApplyConfiguration(); throw new Exception("无效年龄应用未失败。"); }
        catch (InvalidDataException) { }
        try { RequireAppliedConfiguration(); throw new Exception("失败应用后仍允许导出旧工程。"); }
        catch (InvalidOperationException) { }
        if (_project.Rules.SelectMany(x => Builder.Select(_catalog, x)).Distinct().Count() != 5)
            throw new InvalidDataException("失败应用破坏了之前五个兵种。");
        AgeText.Text = ""; ApplyConfiguration(); RequireAppliedConfiguration();
        _project = savedProject; SelectTroop(_catalog.Troops["imperial_recruit"]);
        // Restore a useful demo: native weapons per troop, one race for the complete regular empire branch.
        ReplaceEquipment.IsChecked = false; ScopeChoice.SelectedIndex = 1; ApplyConfiguration();
        var directory = Path.GetDirectoryName(Path.GetFullPath(pngPath))!; Directory.CreateDirectory(directory);
        Json.Save(Path.Combine(directory, "gui-demo.project.json"), _project);
        TroopSearch.Text = "imperial_recruit";
        if (TroopTree.Items.Count == 0) throw new InvalidDataException("GUI 搜索未生效。");
        TroopSearch.Text = "";
        SelectTroop(_catalog.Troops["imperial_recruit"]);
        foreach (TreeViewItem culture in TroopTree.Items)
            if (culture.Items.Cast<TreeViewItem>().Any(x => (x.Tag as TroopInfo)?.Id == "imperial_recruit"))
            { culture.IsExpanded = true; var node = culture.Items.Cast<TreeViewItem>().First(x => (x.Tag as TroopInfo)?.Id == "imperial_recruit"); node.IsExpanded = true; node.IsSelected = true; node.BringIntoView(); }
        ShowReport(Builder.Validate(_catalog, _project)); UpdateProjectText();
        SettingsScroll.ScrollToEnd();
        await Dispatcher.InvokeAsync(() => { UpdateLayout(); }, System.Windows.Threading.DispatcherPriority.ApplicationIdle);
        await Dispatcher.InvokeAsync(() => { UpdateLayout(); }, System.Windows.Threading.DispatcherPriority.ApplicationIdle);
        var bitmap = new RenderTargetBitmap((int)ActualWidth, (int)ActualHeight, 96, 96, PixelFormats.Pbgra32);
        bitmap.Render(this); var encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(bitmap));
        using var stream = File.Create(pngPath); encoder.Save(stream);
        Json.Save(Path.Combine(directory, "gui-smoke.json"), new { status = "pass", scan = true, treeSelection = true, subtreeApply = true, cataphractTianxiangExport = true, rejectedApplyBlocksExport = true, slotEdit = true, loadoutCopy = true, overlapUpdate = true, aiFieldsRetained = true, search = true, bilingualNames = true, armorOverride = true, originalArmorAutofill = true, originalArmorEditAndRoundtrip = true, originalArmorSelectionRefresh = true, skillsOverride = true, skillReset = true, skillBatchPreservesOtherNodes = true, mercenaryChineseSearch = true, screenshot = pngPath });
    }
}
