import React, { useState, useEffect } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

const ProductManager = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    key_features: [],
    selling_points: [],
    common_objections: [],
    faqs: [],
    target_audience: '',
    custom_fields: []
  });

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get('/sales/products');
      if (response.data.success) {
        setProducts(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingProduct 
        ? `/sales/products/${editingProduct._id}`
        : '/sales/products';
      const method = editingProduct ? 'put' : 'post';
      
      const response = await axios[method](url, formData);
      if (response.data.success) {
        fetchProducts();
        setShowModal(false);
        setEditingProduct(null);
        resetForm();
      }
    } catch (error) {
      console.error('Error saving product:', error);
    }
  };

  const handleDelete = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        const response = await axios.delete(`/sales/products/${productId}`);
        if (response.data.success) {
          fetchProducts();
        }
      } catch (error) {
        console.error('Error deleting product:', error);
      }
    }
  };

  const handleActivate = async (productId) => {
    try {
      const response = await axios.post(`/sales/products/${productId}/activate`);
      if (response.data.success) {
        fetchProducts();
      }
    } catch (error) {
      console.error('Error activating product:', error);
    }
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
    setFormData(product);
    setShowModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      price: '',
      key_features: [],
      selling_points: [],
      common_objections: [],
      faqs: [],
      target_audience: '',
      custom_fields: []
    });
  };

  const addKeyFeature = () => {
    setFormData({
      ...formData,
      key_features: [...formData.key_features, '']
    });
  };

  const updateKeyFeature = (index, value) => {
    const newFeatures = [...formData.key_features];
    newFeatures[index] = value;
    setFormData({ ...formData, key_features: newFeatures });
  };

  const removeKeyFeature = (index) => {
    const newFeatures = formData.key_features.filter((_, i) => i !== index);
    setFormData({ ...formData, key_features: newFeatures });
  };

  const addSellingPoint = () => {
    setFormData({
      ...formData,
      selling_points: [...formData.selling_points, '']
    });
  };

  const updateSellingPoint = (index, value) => {
    const newPoints = [...formData.selling_points];
    newPoints[index] = value;
    setFormData({ ...formData, selling_points: newPoints });
  };

  const removeSellingPoint = (index) => {
    const newPoints = formData.selling_points.filter((_, i) => i !== index);
    setFormData({ ...formData, selling_points: newPoints });
  };

  const addFAQ = () => {
    setFormData({
      ...formData,
      faqs: [...formData.faqs, { question: '', answer: '' }]
    });
  };

  const updateFAQ = (index, field, value) => {
    const newFAQs = [...formData.faqs];
    newFAQs[index][field] = value;
    setFormData({ ...formData, faqs: newFAQs });
  };

  const removeFAQ = (index) => {
    const newFAQs = formData.faqs.filter((_, i) => i !== index);
    setFormData({ ...formData, faqs: newFAQs });
  };

  const addCustomField = () => {
    setFormData({
      ...formData,
      custom_fields: [...formData.custom_fields, { field_name: '', field_value: '' }]
    });
  };

  const updateCustomField = (index, field, value) => {
    const newFields = [...formData.custom_fields];
    newFields[index][field] = value;
    setFormData({ ...formData, custom_fields: newFields });
  };

  const removeCustomField = (index) => {
    const newFields = formData.custom_fields.filter((_, i) => i !== index);
    setFormData({ ...formData, custom_fields: newFields });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-heading-lg font-bold text-dark-text">Product Manager</h1>
        <button
          onClick={() => {
            resetForm();
            setEditingProduct(null);
            setShowModal(true);
          }}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Product
        </button>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product) => (
          <div key={product._id} className={`card ${product.isActive ? 'border-dark-success' : ''}`}>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-heading-md font-semibold text-dark-text">{product.name}</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(product)}
                  className="text-dark-accent hover:text-blue-400 hover:brightness-110"
                  title="Edit"
                >
                  <PencilIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => handleDelete(product._id)}
                  className="text-red-500 hover:text-red-400 hover:brightness-110"
                  title="Delete"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
                {!product.isActive && (
                  <button
                    onClick={() => handleActivate(product._id)}
                    className="text-dark-success hover:text-green-400 hover:brightness-110"
                    title="Activate"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                )}
              </div>
            </div>
            
            <p className="text-dark-text-muted mb-4">{product.description}</p>
            
            <div className="flex justify-between items-center mb-4">
              <span className="text-2xl font-bold text-dark-success">
                {product.price || 'Contact for pricing'}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                product.isActive ? 'bg-green-900 text-green-200' : 'bg-gray-700 text-gray-300'
              }`}>
                {product.isActive ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
            
            <div className="text-sm text-dark-text-muted">
              <p>Key Features: {product.key_features?.length || 0}</p>
              <p>Selling Points: {product.selling_points?.length || 0}</p>
              <p>FAQs: {product.faqs?.length || 0}</p>
              <p>Custom Fields: {product.custom_fields?.length || 0}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2 className="text-heading-lg font-bold text-dark-text">
                {editingProduct ? 'Edit Product' : 'Add New Product'}
              </h2>
            </div>
            
            <div className="modal-body">
              <form id="product-form" onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label">
                    Product Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                
                <div>
                  <label className="form-label">
                    Price
                  </label>
                  <input
                    type="text"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    placeholder="e.g., ₹2000-₹10000 per night"
                    className="input-field"
                  />
                </div>
              </div>

              <div>
                <label className="form-label">
                  Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="input-field"
                  required
                />
              </div>

              <div>
                <label className="form-label">
                  Target Audience
                </label>
                <input
                  type="text"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                  placeholder="e.g., Business travelers, families, budget-conscious travelers"
                  className="input-field"
                />
              </div>

              {/* Key Features */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="form-label">
                    Key Features
                  </label>
                  <button
                    type="button"
                    onClick={addKeyFeature}
                    className="text-dark-accent hover:text-blue-400 text-sm hover:brightness-110"
                  >
                    + Add Feature
                  </button>
                </div>
                {formData.key_features.map((feature, index) => (
                  <div key={index} className="flex gap-2 mb-2">
                    <input
                      type="text"
                      placeholder="Feature description"
                      value={feature}
                      onChange={(e) => updateKeyFeature(index, e.target.value)}
                      className="input-field flex-1"
                    />
                    <button
                      type="button"
                      onClick={() => removeKeyFeature(index)}
                      className="text-red-500 hover:text-red-400 hover:brightness-110"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Selling Points */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="form-label">
                    Selling Points
                  </label>
                  <button
                    type="button"
                    onClick={addSellingPoint}
                    className="text-dark-accent hover:text-blue-400 text-sm hover:brightness-110"
                  >
                    + Add Selling Point
                  </button>
                </div>
                {formData.selling_points.map((point, index) => (
                  <div key={index} className="flex gap-2 mb-2">
                    <input
                      type="text"
                      placeholder="Selling point"
                      value={point}
                      onChange={(e) => updateSellingPoint(index, e.target.value)}
                      className="input-field flex-1"
                    />
                    <button
                      type="button"
                      onClick={() => removeSellingPoint(index)}
                      className="text-red-500 hover:text-red-400 hover:brightness-110"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>

              {/* FAQs */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="form-label">
                    FAQs
                  </label>
                  <button
                    type="button"
                    onClick={addFAQ}
                    className="text-dark-accent hover:text-blue-400 text-sm hover:brightness-110"
                  >
                    + Add FAQ
                  </button>
                </div>
                {formData.faqs.map((faq, index) => (
                  <div key={index} className="mb-4 p-4 border border-dark-border rounded-lg bg-dark-card">
                    <div className="mb-2">
                      <input
                        type="text"
                        placeholder="Question"
                        value={faq.question}
                        onChange={(e) => updateFAQ(index, 'question', e.target.value)}
                        className="input-field"
                      />
                    </div>
                    <div className="flex gap-2">
                      <textarea
                        placeholder="Answer"
                        value={faq.answer}
                        onChange={(e) => updateFAQ(index, 'answer', e.target.value)}
                        rows={2}
                        className="input-field flex-1"
                      />
                      <button
                        type="button"
                        onClick={() => removeFAQ(index)}
                        className="text-red-500 hover:text-red-400 hover:brightness-110"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Custom Fields */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="form-label">
                    Custom Fields
                  </label>
                  <button
                    type="button"
                    onClick={addCustomField}
                    className="text-dark-accent hover:text-blue-400 text-sm hover:brightness-110"
                  >
                    + Add Custom Field
                  </button>
                </div>
                {formData.custom_fields.map((field, index) => (
                  <div key={index} className="grid grid-cols-2 gap-2 mb-2">
                    <input
                      type="text"
                      placeholder="Field name (e.g., Warranty)"
                      value={field.field_name}
                      onChange={(e) => updateCustomField(index, 'field_name', e.target.value)}
                      className="input-field"
                    />
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Field value (e.g., 2 years)"
                        value={field.field_value}
                        onChange={(e) => updateCustomField(index, 'field_value', e.target.value)}
                        className="input-field flex-1"
                      />
                      <button
                        type="button"
                        onClick={() => removeCustomField(index)}
                        className="text-red-500 hover:text-red-400 hover:brightness-110"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              </form>
            </div>
            
            <div className="modal-footer">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="btn-outline"
              >
                Cancel
              </button>
              <button
                type="submit"
                form="product-form"
                className="btn-primary"
              >
                {editingProduct ? 'Update Product' : 'Create Product'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductManager;
