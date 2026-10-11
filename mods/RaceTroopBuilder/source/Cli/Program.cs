using RaceTroopBuilder.Core;

var options = new Dictionary<string, List<string>>(StringComparer.Ordinal);
try
{
    var command = args.FirstOrDefault() ?? "help";
    for (var i = 1; i < args.Length; i++)
    {
        if (!args[i].StartsWith("--", StringComparison.Ordinal) || i + 1 == args.Length || args[i + 1].StartsWith("--", StringComparison.Ordinal))
            throw new ArgumentException("参数必须采用 --名称 值：" + args[i]);
        var key = args[i][2..];
        if (!options.TryGetValue(key, out var list)) options[key] = list = [];
        list.Add(args[++i]);
    }
    string? Get(string key) => options.TryGetValue(key, out var list) ? list.Last() : null;
    string Require(string key) => Get(key) ?? throw new ArgumentException("缺少 --" + key);
    void Allowed(params string[] keys)
    {
        foreach (var key in options.Keys)
            if (!keys.Contains(key)) throw new ArgumentException("此命令不支持 --" + key);
        foreach (var (key, list) in options)
            if (key != "mods" && list.Count > 1) throw new ArgumentException("参数重复：--" + key);
    }
    Catalog Scan(BuilderProject? project = null) => Discovery.Scan(Get("game") ?? project?.GameRoot,
        options.TryGetValue("mods", out var roots) ? roots : project?.ModRoots);
    void Result(object value) => Console.WriteLine(Json.Write(value));
    switch (command)
    {
        case "help":
            Allowed();
            Result(new { tool = "RaceTroopBuilder", version = "0.2.0", commands = new[]
            {
                "scan [--game PATH] [--mods PATH ...]",
                "catalog --kind troops|items|races [--filter TEXT] [--lang zh-CN|en] [--game PATH] [--mods PATH ...]",
                "troop --id ID [--game PATH] [--mods PATH ...]",
                "new --out PROJECT.json [--id MyRaceTroops] [--name English Name] [--game PATH] [--mods PATH ...]",
                "configure --project PROJECT.json --rule RULE.json [--index 0] [--game PATH] [--mods PATH ...]",
                "validate|preview --project PROJECT.json [--game PATH] [--mods PATH ...]",
                "build --project PROJECT.json --out OUTPUT_ROOT [--game PATH] [--mods PATH ...]",
                "package --report VALIDATION.json --out PACKAGE.zip",
                "install --report VALIDATION.json [--game PATH] [--backups PATH]"
            }, exitCodes = new { success = 0, invalidProject = 2, operationError = 1 } });
            break;
        case "new":
        {
            Allowed("out", "id", "name", "game", "mods");
            var path = Require("out");
            if (File.Exists(path)) throw new IOException("工程已存在：" + path);
            var project = new BuilderProject { ModuleId = Get("id") ?? "MyRaceTroops", ModuleName = Get("name") ?? "My Race Troops",
                GameRoot = Discovery.FindGame(Get("game")), ModRoots = options.GetValueOrDefault("mods")?.Select(Path.GetFullPath).ToList() ?? [Discovery.DefaultModRoot()] };
            Json.Save(path, project); Result(new { status = "pass", projectPath = Path.GetFullPath(path) }); break;
        }
        case "scan":
        {
            Allowed("game", "mods"); var catalog = Scan();
            Result(new { catalog.GameRoot, catalog.GameVersion, catalog.ModRoots, troopCount = catalog.Troops.Count, itemCount = catalog.Items.Count,
                races = catalog.Races, modules = catalog.Modules.Values.Select(x => new { x.Id, x.Name, x.Version, x.Path, x.Dependencies }), issues = catalog.Issues }); break;
        }
        case "catalog":
        {
            Allowed("kind", "filter", "game", "mods", "lang"); var catalog = Scan(); var filter = Get("filter") ?? "";
            var language = Get("lang") ?? "zh-CN";
            if (language is not ("zh-CN" or "en")) throw new ArgumentException("lang 应为 zh-CN 或 en。");
            foreach (var item in catalog.Items.Values) item.Language = language;
            bool Matches(string text) => text.Contains(filter, StringComparison.OrdinalIgnoreCase);
            switch (Require("kind"))
            {
                case "races": Result(catalog.Races.Where(x => Matches(x.Label))); break;
                case "items": Result(catalog.Items.Values.Where(x => Matches(x.SearchText)).OrderBy(x => x.Id)); break;
                case "troops": Result(catalog.Troops.Values.Where(x => Matches(x.SearchText)).OrderBy(x => x.Id)
                    .Select(x => new { x.Id, x.Name, x.NameEn, x.NameZh, x.NameKey, displayName = x.DisplayName(language), x.Culture, x.Level, x.IsFemale, x.IsBasicTroop, x.Upgrades })); break;
                default: throw new ArgumentException("kind 应为 troops、items 或 races。");
            }
            break;
        }
        case "troop":
        {
            Allowed("id", "game", "mods"); var catalog = Scan();
            if (!catalog.Troops.TryGetValue(Require("id"), out var troop)) throw new ArgumentException("找不到兵种。");
            Result(new { troop.Id, troop.Name, troop.NameEn, troop.NameZh, troop.NameKey, troop.Culture, troop.Level, troop.Upgrades,
                loadouts = Builder.Loadouts(catalog, troop.Element).Select(x => new { type = x.Type, x.Loadout.Slots }), xml = troop.Element.ToString() }); break;
        }
        case "configure":
        {
            Allowed("project", "rule", "index", "game", "mods");
            var path = Require("project"); var project = Builder.ReadProject(path); var rule = Json.Read<TroopRule>(Require("rule"));
            if (Get("index") is string text)
            {
                if (!int.TryParse(text, out var index) || index < 0 || index >= project.Rules.Count) throw new ArgumentException("规则 index 超出范围。");
                project.Rules[index] = rule;
            }
            else project.Rules.Add(rule);
            var catalog = Scan(project); var report = Builder.Validate(catalog, project);
            if (report.Status == "pass")
            { project.GameRoot = catalog.GameRoot; project.ModRoots = catalog.ModRoots; Json.Save(path, project); }
            else Environment.ExitCode = 2;
            Result(report); break;
        }
        case "validate": case "preview": case "build":
        {
            Allowed(command == "build" ? ["project", "game", "mods", "out"] : ["project", "game", "mods"]);
            var project = Builder.ReadProject(Require("project")); var catalog = Scan(project);
            project.GameRoot = catalog.GameRoot; project.ModRoots = catalog.ModRoots;
            if (command == "preview")
            { var report = Builder.Validate(catalog, project); Result(Builder.Preview(catalog, project)); if (report.Status != "pass") Environment.ExitCode = 2; }
            else
            { var report = command == "build" ? Builder.Build(catalog, project, Require("out")) : Builder.Validate(catalog, project);
                Result(report); if (report.Status != "pass") Environment.ExitCode = 2; }
            break;
        }
        case "package":
            Allowed("report", "out"); Result(new { status = "pass", archive = Builder.Package(Require("report"), Require("out")) }); break;
        case "install":
            Allowed("report", "game", "backups"); Result(Builder.Install(Require("report"), Get("game"), Get("backups"))); break;
        default: throw new ArgumentException("未知命令：" + command + "；运行 help 查看接口。");
    }
}
catch (Exception error)
{
    Console.WriteLine(Json.Write(new { status = "fail", issues = new[] { new Issue("error", "operation_error", error.Message) } }));
    Environment.ExitCode = 1;
}
