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
        UpdateProjectText();
    }

    private static string SlotLabel(string slot) => slot switch
    {
        "Item0" => "Item0 · 武器槽 1", "Item1" => "Item1 · 武器槽 2", "Item2" => "Item2 · 武器槽 3", "Item3" => "Item3 · 武器槽 4",
        "Head" => "Head · 头部", "Cape" => "Cape · 披肩", "Body" => "Body · 身甲", "Leg" => "Leg · 腿部", "Gloves" => "Gloves · 手套",
        "Horse" => "Horse · 坐骑", _ => "HorseHarness · 马具"
    };
    private void SyncMetadata()
    { ModuleIdText.Text = _project.ModuleId; ModuleNameText.Text = _project.ModuleName; VersionText.Text = _project.Version; }
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
        RenderTree();
        OutputText.Text = $"扫描完成：{_catalog.Troops.Count} 个普通士兵，{_catalog.Items.Count} 个原版物品，{_catalog.Races.Count} 个自定义种族。\n\n依赖种族 Mod 在上，生成的兵种替换 Mod 在下。\n请选择兵种和种族，再应用配置。\n\n" +
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
            var matching = culture.Where(x => filter.Length == 0 || (x.Id + " " + x.Name + " " + x.Culture).Contains(filter, StringComparison.OrdinalIgnoreCase)).ToList();
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
        var node = new TreeViewItem { Header = (configured ? "● " : "") + troop.Label, Tag = troop, ToolTip = troop.Id };
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
        SelectedName.Text = troop.Name; SelectedMeta.Text = $"{troop.Id} · Lv{troop.Level}";
        SelectedMeta.ToolTip = $"{CultureLabel(troop.Culture)} · {troop.Upgrades.Count} 个升级目标";
        var rule = _project.Rules.FirstOrDefault(x => Builder.Select(_catalog!, x).Contains(troop.Id));
        if (rule != null)
        {
            RaceChoice.SelectedItem = _catalog!.Races.FirstOrDefault(x => x.ModuleId == rule.RaceModule && x.Id == rule.RaceId);
            GenderChoice.SelectedIndex = rule.IsFemale == null ? 0 : rule.IsFemale.Value ? 1 : 2;
            FaceChoice.SelectedIndex = rule.FaceMode == "fixed" ? 1 : 0;
            AgeText.Text = rule.Age?.ToString() ?? ""; StripArmor.IsChecked = rule.StripArmor;
        }
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
            }).Where(x => x.Label.Contains(filter, StringComparison.OrdinalIgnoreCase)).OrderBy(x => x.Id).ToList();
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
    private void ApplyConfiguration()
    {
        RequireCatalog();
        var targets = ScopeIds();
        if (RaceChoice.SelectedItem is not RaceInfo race) throw new InvalidOperationException("请选择依赖种族。");
        int? age = null;
        if (AgeText.Text.Trim().Length > 0)
        { if (!int.TryParse(AgeText.Text.Trim(), out var number)) throw new InvalidDataException("年龄应为整数。"); age = number; }
        var rule = new TroopRule { TroopIds = targets, RaceModule = race.ModuleId, RaceId = race.Id,
            IsFemale = GenderChoice.SelectedIndex switch { 1 => true, 2 => false, _ => null }, Age = age,
            FaceMode = FaceChoice.SelectedIndex == 1 ? "fixed" : "preserve", StripArmor = StripArmor.IsChecked == true,
            BattleLoadouts = ReplaceEquipment.IsChecked == true ? _editedLoadouts.Select(Clone).ToList() : null };
        CaptureMetadata();
        // Keep the prior project until the candidate passes validation.
        var candidate = System.Text.Json.JsonSerializer.Deserialize<BuilderProject>(Json.Write(_project), Json.Options)!;
        var previous = _project; _project = candidate;
        var preserved = targets.GroupBy(id =>
        {
            var original = previous.Rules.FirstOrDefault(x => Builder.Select(_catalog!, x).Contains(id));
            return Json.Write(new { original?.Name, original?.CivilianLoadouts });
        }).ToList();
        RemoveTargets(targets);
        foreach (var group in preserved)
        {
            var newRule = System.Text.Json.JsonSerializer.Deserialize<TroopRule>(Json.Write(rule), Json.Options)!;
            var original = previous.Rules.FirstOrDefault(x => Builder.Select(_catalog!, x).Contains(group.First()));
            newRule.TroopIds = group.ToList(); newRule.Name = original?.Name;
            newRule.CivilianLoadouts = original?.CivilianLoadouts?.Select(Clone).ToList();
            _project.Rules.Add(newRule);
        }
        var report = Builder.Validate(_catalog!, _project);
        if (report.Status != "pass") { _project = previous; ShowReport(report); return; }
        _lastReport = null; UpdateProjectText(); ShowReport(report);
        var selectedId = _selected!.Id; RenderTree(); SelectTroop(_catalog!.Troops[selectedId]);
    }
    private async void ApplyClick(object sender, RoutedEventArgs e) => await Run(ApplyConfiguration);
    private async void RemoveRuleClick(object sender, RoutedEventArgs e) => await Run(() =>
    { var ids = ScopeIds(); RemoveTargets(ids); _lastReport = null; UpdateProjectText(); RenderTree(); OutputText.Text = $"已撤销 {ids.Count} 个兵种的替换配置。"; });
    private void ShowReport(CheckReport report)
    {
        OutputText.Text = $"{(report.Status == "pass" ? "检查通过" : "检查未通过")} · {report.Targets.Count} 个目标兵种 · {report.TransformChecks} 个节点转换核对\n\n加载顺序（从上到下）：\n" + string.Join(" → ", report.LoadOrder) +
            "\n\n" + string.Join("\n", report.Issues.Select(x => $"[{x.Severity}] {x.Subject}: {x.Message}")) + "\n\n" + report.RuntimeTesting;
        if (report.ModulePath != null) OutputText.Text += "\n\n导出目录：" + report.ModulePath;
    }
    private async void ValidateClick(object sender, RoutedEventArgs e) => await Run(() =>
    { RequireCatalog(); CaptureMetadata(); UpdateProjectText(); ShowReport(Builder.Validate(_catalog!, _project)); });
    private async void PreviewClick(object sender, RoutedEventArgs e) => await Run(() =>
    {
        RequireCatalog(); CaptureMetadata(); UpdateProjectText(); var report = Builder.Validate(_catalog!, _project); ShowReport(report);
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
    { _project = new(); _projectFile = null; _lastReport = null; SyncMetadata(); UpdateProjectText(); if (_catalog != null) RenderTree(); });
    public async Task OpenProject(string path)
    {
        await Run(async () =>
        {
            var project = Builder.ReadProject(path);
            _project = project; _projectFile = Path.GetFullPath(path); _lastReport = null;
            GamePath.Text = project.GameRoot ?? GamePath.Text; ModPaths.Text = string.Join(Environment.NewLine, project.ModRoots.Count > 0 ? project.ModRoots : [Discovery.DefaultModRoot()]);
            SyncMetadata(); await ScanCatalog(); UpdateProjectText(); ShowReport(Builder.Validate(_catalog!, _project));
        });
    }
    private async void OpenClick(object sender, RoutedEventArgs e)
    { var dialog = new OpenFileDialog { Filter = "拼装工程 JSON|*.json", Title = "打开兵种拼装工程" }; if (dialog.ShowDialog(this) == true) await OpenProject(dialog.FileName); }
    private async void SaveClick(object sender, RoutedEventArgs e) => await Run(() =>
    {
        var dialog = new SaveFileDialog { Filter = "拼装工程 JSON|*.json", FileName = _projectFile ?? "my-race-troops.json" };
        if (dialog.ShowDialog(this) != true) return;
        CaptureMetadata(); Json.Save(dialog.FileName, _project); _projectFile = dialog.FileName; UpdateProjectText();
    });
    private async void BuildClick(object sender, RoutedEventArgs e) => await Run(async () =>
    {
        RequireCatalog(); CaptureMetadata(); UpdateProjectText();
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
        await Dispatcher.InvokeAsync(() => { UpdateLayout(); }, System.Windows.Threading.DispatcherPriority.ApplicationIdle);
        var bitmap = new RenderTargetBitmap((int)ActualWidth, (int)ActualHeight, 96, 96, PixelFormats.Pbgra32);
        bitmap.Render(this); var encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(bitmap));
        using var stream = File.Create(pngPath); encoder.Save(stream);
        Json.Save(Path.Combine(directory, "gui-smoke.json"), new { status = "pass", scan = true, treeSelection = true, subtreeApply = true, slotEdit = true, loadoutCopy = true, overlapUpdate = true, aiFieldsRetained = true, search = true, screenshot = pngPath });
    }
}
