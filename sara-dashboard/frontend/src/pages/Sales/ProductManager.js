import React, { useState, useEffect } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';

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
      const response = await fetch('/api/sales/products');
      const data = await response.json();
      if (data.success) {
        setProducts(data.data);
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
        ? `/api/sales/products/${editingProduct._id}`
        : '/api/sales/products';
      const method = editingProduct ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      if (result.success) {
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
        const response = await fetch(`/api/sales/products/${productId}`, {
          method: 'DELETE'
        });
        const result = await response.json();
        if (result.success) {
          fetchProducts();
        }
      } catch (error) {
        console.error('Error deleting product:', error);
      }
    }
  };

  const handleActivate = async (productId) => {
    try {
      const response = await fetch(`/api/sales/products/${productId}/activate`, { method: 'POST' });
      const result = await response.json();
      if (result.success) {
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
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Product Manager</h1>
        <button
          onClick={() => {
            resetForm();
            setEditingProduct(null);
            setShowModal(true);
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Product
        </button>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product) => (
          <div key={product._id} className={`bg-white rounded-lg shadow-md p-6 border ${product.isActive ? 'border-green-500' : ''}`}>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold text-gray-900">{product.name}</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(product)}
                  className="text-blue-600 hover:text-blue-800"
                  title="Edit"
                >
                  <PencilIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => handleDelete(product._id)}
                  className="text-red-600 hover:text-red-800"
                  title="Delete"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
                {!product.isActive && (
                  <button
                    onClick={() => handleActivate(product._id)}
                    className="text-green-600 hover:text-green-800"
                    title="Activate"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                )}
              </div>
            </div>
            
            <p className="text-gray-600 mb-4">{product.description}</p>
            
            <div className="flex justify-between items-center mb-4">
              <span className="text-2xl font-bold text-green-600">
                {product.price || 'Contact for pricing'}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                product.isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {product.isActive ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
            
            <div className="text-sm text-gray-500">
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6">
              {editingProduct ? 'Edit Product' : 'Add New Product'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Product Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Price
                  </label>
                  <input
                    type="text"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    placeholder="e.g., ₹2000-₹10000 per night"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Audience
                </label>
                <input
                  type="text"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                  placeholder="e.g., Business travelers, families, budget-conscious travelers"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Key Features */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Key Features
                  </label>
                  <button
                    type="button"
                    onClick={addKeyFeature}
                    className="text-blue-600 hover:text-blue-800 text-sm"
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
                      className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1"
                    />
                    <button
                      type="button"
                      onClick={() => removeKeyFeature(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Selling Points */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Selling Points
                  </label>
                  <button
                    type="button"
                    onClick={addSellingPoint}
                    className="text-blue-600 hover:text-blue-800 text-sm"
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
                      className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1"
                    />
                    <button
                      type="button"
                      onClick={() => removeSellingPoint(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>

              {/* FAQs */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    FAQs
                  </label>
                  <button
                    type="button"
                    onClick={addFAQ}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    + Add FAQ
                  </button>
                </div>
                {formData.faqs.map((faq, index) => (
                  <div key={index} className="mb-4 p-4 border border-gray-200 rounded-lg">
                    <div className="mb-2">
                      <input
                        type="text"
                        placeholder="Question"
                        value={faq.question}
                        onChange={(e) => updateFAQ(index, 'question', e.target.value)}
                        className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div className="flex gap-2">
                      <textarea
                        placeholder="Answer"
                        value={faq.answer}
                        onChange={(e) => updateFAQ(index, 'answer', e.target.value)}
                        rows={2}
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1"
                      />
                      <button
                        type="button"
                        onClick={() => removeFAQ(index)}
                        className="text-red-600 hover:text-red-800"
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
                  <label className="block text-sm font-medium text-gray-700">
                    Custom Fields
                  </label>
                  <button
                    type="button"
                    onClick={addCustomField}
                    className="text-blue-600 hover:text-blue-800 text-sm"
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
                      className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Field value (e.g., 2 years)"
                        value={field.field_value}
                        onChange={(e) => updateCustomField(index, 'field_value', e.target.value)}
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1"
                      />
                      <button
                        type="button"
                        onClick={() => removeCustomField(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingProduct ? 'Update Product' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductManager;
