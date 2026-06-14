import fs from 'fs'
import path from 'path'

// Reads DATOS_TOP20_VENTAS.csv and returns:
// - canal_por_producto: sales breakdown by channel (Online/Presencial) per SKU
// - top_clientes: top 15 clients by total sales volume
export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const csvPath = path.resolve(dataRoot, 'EDA_Outputs/DATOS_TOP20_VENTAS.csv')

    const text = fs.readFileSync(csvPath).toString('latin1')
    const lines = text.trim().split(/\r?\n/)
    const sep = lines[0].includes(';') ? ';' : ','
    const headers = lines[0].split(sep).map(h => h.trim())

    const iCodigo   = headers.indexOf('Código')
    const iSalida   = headers.indexOf('Salida')
    const iCanal    = headers.indexOf('Canal_Venta')
    const iCliente  = headers.indexOf('Empresa_Cliente')

    const canalProd = {}
    const clientes  = {}

    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue
      const p = lines[i].split(sep)
      const codigo  = (p[iCodigo]  || '').trim()
      const salida  = parseFloat(p[iSalida]) || 0
      const canal   = (p[iCanal]   || 'Desconocido').trim() || 'Desconocido'
      const cliente = (p[iCliente] || 'Desconocido').trim() || 'Desconocido'

      if (salida <= 0 || !codigo) continue

      const key = `${codigo}|||${canal}`
      if (!canalProd[key]) canalProd[key] = { codigo, canal, ventas: 0, transacciones: 0 }
      canalProd[key].ventas += salida
      canalProd[key].transacciones++

      if (!clientes[cliente]) clientes[cliente] = { cliente, ventas: 0, transacciones: 0 }
      clientes[cliente].ventas += salida
      clientes[cliente].transacciones++
    }

    const topClientes = Object.values(clientes)
      .sort((a, b) => b.ventas - a.ventas)
      .slice(0, 15)
      .map(r => ({ ...r, ventas: Math.round(r.ventas) }))

    const totalClientes = topClientes.reduce((s, c) => s + c.ventas, 0)
    let acum = 0
    topClientes.forEach(c => {
      acum += c.ventas
      c.acumulado_pct = totalClientes > 0 ? Math.round((acum / totalClientes) * 1000) / 10 : 0
    })

    res.status(200).json({
      canal_por_producto: Object.values(canalProd).map(r => ({
        ...r, ventas: Math.round(r.ventas)
      })),
      top_clientes: topClientes,
    })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
