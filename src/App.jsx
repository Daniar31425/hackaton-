import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_URL = 'http://localhost:8000/tasks';

const statusColors = {
  'в процессе': 'bg-yellow-100 text-yellow-800',
  'выполнена': 'bg-green-100 text-green-800',
  'просрочена': 'bg-red-100 text-red-800',
};

function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Получение задач
  const fetchTasks = async () => {
    try {
      const res = await axios.get(API_URL);
      setTasks(res.data);
      setLoading(false);
    } catch (err) {
      setError('Ошибка при загрузке данных');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  // Удаление задачи с подтверждением
const deleteTask = async (id) => {
  const confirmed = window.confirm("Вы уверены, что хотите удалить эту задачу?");
  if (!confirmed) return;

  try {
    await axios.delete(`${API_URL}/${id}`);
    setTasks(prev => prev.filter(task => task.id !== id)); // обновление списка
  } catch (err) {
    console.error("Ошибка при удалении задачи:", err);
    setError("Ошибка при удалении задачи");
  }
};

const updateTaskStatus = async (id, status) => {
  try {
    await axios.put(`${API_URL}/${id}`, { status });
    setTasks(prev => prev.map(task => task.id === id ? { ...task, status } : task));
  } catch (err) {
    console.error("Ошибка при обновлении статуса задачи:", err);
    setError("Ошибка при обновлении статуса задачи");
  }
};

  // Статистика по статусу задач
  const stats = {
    total: tasks.length,
    in_progress: tasks.filter(t => t.status === 'в процессе').length,
    done: tasks.filter(t => t.status === 'выполнена').length,
    overdue: tasks.filter(t => t.status === 'просрочена').length,
  };

  // Время выполнения задач
  const resolveTimes = tasks.filter(t => t.status === 'выполнена').map(task => {
    const start = new Date(task.created_at);
    const end = new Date(task.updated_at || task.deadline);
    const hours = Math.round((end - start) / (1000 * 60 * 60));
    return {
      name: task.department,
      hours,
    };
  });

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-6">Список задач</h1>

      {/* Панель аналитики */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow p-4 text-center">
          <p className="text-gray-500 text-sm">Всего</p>
          <p className="text-2xl font-bold">{stats.total}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-4 text-center">
          <p className="text-yellow-600 text-sm">В процессе</p>
          <p className="text-xl font-semibold">{stats.in_progress}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-4 text-center">
          <p className="text-green-600 text-sm">Выполнено</p>
          <p className="text-xl font-semibold">{stats.done}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-4 text-center">
          <p className="text-red-600 text-sm">Просрочено</p>
          <p className="text-xl font-semibold">{stats.overdue}</p>
        </div>
      </div>

      {/* График решения */}
      <div className="bg-white rounded-xl shadow p-6 mb-10">
        <h2 className="text-xl font-semibold mb-4">Среднее время решения задач (в часах)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={resolveTimes} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="hours" fill="#60a5fa" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Список задач */}
      <div className="grid gap-4">
        {tasks.map(task => (
          <div key={task.id} className="bg-white p-4 rounded-xl shadow-md">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-xl font-semibold">{task.content}</h2>
              <button
                onClick={() => deleteTask(task.id)}
                className="text-red-500 hover:text-red-700 text-sm"
              >
                Удалить
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-1">Управление: {task.department}</p>
            <p className="text-sm text-gray-600 mb-1">Создано: {new Date(task.created_at).toLocaleString()}</p>
            <p className="text-sm text-gray-600 mb-3">Срок: {new Date(task.deadline).toLocaleString()}</p>
<div className="flex items-center">
  <span className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${statusColors[task.status]}`}>
    {task.status}
  </span>
  <button
    onClick={() => updateTaskStatus(task.id, 'выполнена')}
    className="ml-2 text-green-500 hover:text-green-700 text-sm"
  >
    Выполнить
  </button>
</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;


const [deptStats, setDeptStats] = useState({});
const [loadingStats, setLoadingStats] = useState(true);

useEffect(() => {
  const fetchStats = async () => {
    try {
      const res = await axios.get("http://localhost:8000/stats/full");
      setDeptStats(res.data);
      setLoadingStats(false);
    } catch (err) {
      setLoadingStats(false);
      console.error("Ошибка загрузки статистики");
    }
  };

  fetchTasks(); // уже есть
  fetchStats(); // новый вызов
}, []);


{/* Подробная статистика по отделам */}
<><><div className="bg-white rounded-xl shadow p-6 mt-10">
  <h2 className="text-xl font-bold mb-4">📊 Статистика по отделам</h2>

  <div className="overflow-auto">
    <table className="min-w-full table-auto border text-sm text-left">
      <thead>
        <tr className="bg-gray-100">
          <th className="p-2 border">Управление</th>
          <th className="p-2 border">Всего</th>
          <th className="p-2 border">Выполнено</th>
          <th className="p-2 border">В процессе</th>
          <th className="p-2 border">Просрочено</th>
          <th className="p-2 border">Среднее время (ч)</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(deptStats).map(([dept, stats]) => (
          <tr key={dept}>
            <td className="p-2 border">{dept}</td>
            <td className="p-2 border">{stats.total}</td>
            <td className="p-2 border">{stats.done}</td>
            <td className="p-2 border">{stats.in_progress}</td>
            <td className="p-2 border">{stats.overdue}</td>
            <td className="p-2 border">{stats.avg_hours}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</div><div className="text-right mt-4">
    <a
      href="http://localhost:8000/stats/report"
      target="_blank"
      rel="noopener noreferrer"
      className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
    >
      📄 Скачать PDF-отчёт
    </a>
  </div></><div className="text-right mt-4">
    <a
      href="http://localhost:8000/stats/report"
      target="_blank"
      rel="noopener noreferrer"
      className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
    >
      📄 Скачать PDF-отчёт
    </a>
  </div></>

{!task.reply && (
  <div className="mt-2">
    <input
      type="text"
      placeholder="Ответ модератора..."
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          axios.post(`http://localhost:8000/tasks/${task.id}/reply`, e.target.value)
            .then(() => {
              alert("Ответ отправлен!");
              fetchTasks(); // обновим
            })
            .catch(() => alert("Ошибка при отправке"));
        }
      }}
      className="border px-2 py-1 text-sm rounded w-full"
    />
  </div>
)}
{task.reply && (
  <p className="text-sm text-green-600 mt-2">💬 Ответ: {task.reply}</p>
)}


{/* График по жалобам по отделам */}
<div className="bg-white rounded-xl shadow p-6 mt-10">
  <h2 className="text-xl font-bold mb-4">📈 Жалобы по отделам</h2>
  <ResponsiveContainer width="100%" height={300}>
    <BarChart
      data={Object.entries(deptStats).map(([dept, stats]) => ({
        name: dept,
        всего: stats.total,
        выполнено: stats.done,
        просрочено: stats.overdue
      }))}
      margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="name" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="всего" fill="#3b82f6" />
      <Bar dataKey="выполнено" fill="#10b981" />
      <Bar dataKey="просрочено" fill="#ef4444" />
    </BarChart>
  </ResponsiveContainer>
</div>
