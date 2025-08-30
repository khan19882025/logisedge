@echo off
echo Starting LogisEdge Backup Scheduler...
echo Time: %date% %time%

cd /d "C:\Users\Admin\OneDrive\Desktop\logisEdge"

echo Running scheduled backups...
python manage.py run_scheduled_backups

echo Backup scheduler completed.
echo Time: %date% %time%
pause
