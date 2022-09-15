from email.policy import default
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Penjualan(models.Model):
    _name = 'belanja.penjualan'
    _description = 'New Description'

    name = fields.Char(string='No. Nota')
    nama_pembeli = fields.Char(string='Nama Pembeli')
    tgl_penjualan = fields.Datetime(string='Tanggal Transaksi', default=fields.Datetime.now())
    total_bayar = fields.Integer(compute='_compute_totalbayar',string='Total Pembayaran')
    detailpenjualan_ids = fields.One2many(comodel_name='belanja.detailpenjualan', 
                                            inverse_name='penjualan_id', 
                                            string='Detail Penjualan')
    state = fields.Selection(string='Status Penjualan', 
                            selection=[('draft', 'Draft'), 
                                       ('confirm', 'Confirm'),
                                       ('done', 'Done'),
                                       ('cancelled', 'Cancelled'),
                                       ],
                            required=True, readonly=True, default='draft')
    
    
    def action_confirm(self):
        for record in self:
            record.write( { 'state': 'confirm'})
        return True
    
    def action_done(self):
        for record in self:
            record.write({
                'state': 'done'
            })
        return True 
    
    def action_cancel(self):
        for record in self:
            record.write({
                'state': 'cancelled'
            })
        return True 

    def action_draft(self):
        for record in self:
            record.write({
                'state': 'draft'
            })    
    
    @api.depends('detailpenjualan_ids')
    def _compute_totalbayar(self):
        for rec in self:
            a = sum(self.env['belanja.detailpenjualan'].search([('penjualan_id','=',rec.id)]).mapped('subtotal'))
            rec.total_bayar=a

    @api.ondelete(at_uninstall=False)
    def __ondelete_penjualan(self):
        if self.detailpenjualan_ids:
            a=[]
            for rec in self:
                a = self.env['belanja.detailpenjualan'].search([('penjualan_id','=',rec.id)])
                print(a)
            for ob in a:
                print(str(ob.barang_id.name) + ' ' +str(ob.qty))
                ob.barang_id.stok += ob.qty
        
    def unlink(self):
        if self.detailpenjualan_ids:
            a=[]
            for rec in self:
                a = self.env['belanja.detailpenjualan'].search([('penjualan_id','=',rec.id)])
                print(a)
            for ob in a:
                print(str(ob.barang_id.name) + ' ' +str(ob.qty))
                ob.barang_id.stok += ob.qty
        record = super(Penjualan,self).unlink()
        
    # _sql_constraints = [
    #     ('nama_kosong', 'check (nama_pembeli is NOT NULL)', 'Nama Harus Di isi')
    # ]

    def write(self, vals):
        for rec in self:
            a = self.env['belanja.detailpenjualan'].search([('penjualan_id', '=', rec.id)])
            print(a)
            for data in a:
                print(str(data.barang_id.name)+' '+str(data.qty)+' '+str(data.barang_id.stok))
                data.barang_id.stok += data.qty
        record = super(Penjualan,self).write(vals)
        for rec in self:
            b = self.env['belanja.detailpenjualan'].search([('penjualan_id', '=', rec.id)])
            print(a)
            print(b)
            for databaru in b:
                if databaru in a:
                    print(str(databaru.barang_id.name)+' '+str(databaru.qty)+' '+str(databaru.barang_id.stok))
                    databaru.barang_id.stok -= databaru.qty
        return record 

    @api.constrains('name')
    def _check_kasir(self):
        for rec in self:
            no_nota = self.env['belanja.penjualan'].search([('name', '=', rec.name), ('id', '!=', rec.id)])
            if no_nota:
                raise ValidationError('No Nota {} sudah tersedia. Silahkan Diganti'.format(rec.name))
            if rec.name == 0:
                raise ValidationError('Data Belum Terinput')
    
class DetailPenjualan(models.Model):
    _name = 'belanja.detailpenjualan'
    _description = 'New Description'

    name = fields.Char(string='Nama')
    # _name = 'belanja.penjualan'
    penjualan_id = fields.Many2one(comodel_name='belanja.penjualan', string='Detail Penjualan')
    barang_id = fields.Many2one(comodel_name='belanja.barang', string='List Barang')
    harga_satuan = fields.Integer(string='Harga Satuan')
    qty = fields.Integer(string='Quantity')
    subtotal = fields.Integer(compute='_compute_subtotal', string='Subtotal')
    
    @api.depends('harga_satuan','qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.harga_satuan * rec.qty
    
    @api.onchange('barang_id')
    def _onchange_barang_id(self):
        if(self.barang_id.harga_jual):
            self.harga_satuan = self.barang_id.harga_jual

    @api.model
    def create(self, vals):
        record = super(DetailPenjualan,self).create(vals)
        if record.qty:
            self.env['belanja.barang'].search([('id','=',record.barang_id.id)]).write({'stok' : record.barang_id.stok - record.qty})
        return record
    
    @api.constrains('qty')
    def check_quantity(self):
        for rec in self:
            if rec.qty <1:
                raise ValidationError('Kamu belum memasukan jumlah barang {}. Silahkan cek kembali'.format(rec.barang_id.name))
            elif rec.barang_id.stok < rec.qty:
                raise ValidationError('Barang {} tidak tersedia, hanya tersedia sebanyak {}'.format(rec.barang_id.name,rec.barang_id.stok))
    
