using System.Windows;

namespace RaceTroopBuilder.Gui;

public partial class App : Application
{
    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var window = new MainWindow();
        MainWindow = window;
        if (e.Args.Length == 2 && e.Args[0] == "--smoke-test")
        {
            window.Left = -10000; window.Top = -10000; window.ShowActivated = false;
            window.Show();
            try { await window.SmokeTest(e.Args[1]); Shutdown(0); }
            catch (Exception error) { System.IO.File.WriteAllText(e.Args[1] + ".error.txt", error.ToString()); Shutdown(1); }
        }
        else
        {
            window.Show();
            if (e.Args.Length == 1) await window.OpenProject(e.Args[0]);
        }
    }
}
